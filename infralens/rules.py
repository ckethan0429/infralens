from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from infralens.config import get_profile_map
from infralens.data import Workload


@dataclass
class Finding:
    category: str
    severity: str
    message: str
    code: str = "generic"
    data: dict[str, Any] | None = None


@dataclass
class PlacementItem:
    workload: str
    action: str
    code: str = "generic"
    data: dict[str, Any] | None = None


@dataclass
class RecommendationResult:
    items: list[PlacementItem]
    expected_util_before: int
    expected_util_after: int
    expected_training_gain_pct: int
    expected_latency_drop_pct: int


def detect_bottlenecks(
    scenario: dict[str, Any], workloads: list[Workload], profile: str = "default"
) -> list[Finding]:
    findings: list[Finding] = []
    gpus = scenario["gpus"]
    cfg_map = get_profile_map("rule_thresholds")
    cfg = cfg_map.get(profile, cfg_map.get("default", {}))
    low_util_threshold = int(cfg.get("low_util_threshold", 45))
    low_util_fraction = float(cfg.get("low_util_fraction", 0.25))
    mig_util_th = int(cfg.get("mig_underused_util_threshold", 65))
    mig_vram_th = float(cfg.get("mig_underused_vram_threshold_gb", 90))
    train_gpu_req = int(cfg.get("requires_training_gpus", 4))

    for g in gpus:
        if g["numa_node"] != g["cpu_socket"]:
            findings.append(
                Finding(
                    category="NUMA",
                    severity="high",
                    message=(
                        f"GPU {g['id']} has NUMA mismatch (GPU NUMA {g['numa_node']} vs "
                        f"CPU socket {g['cpu_socket']})."
                    ),
                    code="numa_mismatch",
                    data={"gpu_id": g["id"], "numa_node": g["numa_node"], "cpu_socket": g["cpu_socket"]},
                )
            )

    low_util = [g for g in gpus if g["gpu_util"] < low_util_threshold]
    if len(low_util) >= max(1, int(round(len(gpus) * low_util_fraction))):
        findings.append(
            Finding(
                category="GPU_UTIL",
                severity="medium",
                message=(
                    f"{len(low_util)} GPU(s) show low utilization (<{low_util_threshold}%), indicating potential under-allocation."
                ),
                code="low_gpu_util",
                data={"count": len(low_util), "threshold": low_util_threshold},
            )
        )

    if any(w.kind == "inference" for w in workloads):
        underused = any(g["gpu_util"] < mig_util_th and g["vram_used_gb"] < mig_vram_th for g in gpus)
        if underused:
            findings.append(
                Finding(
                    category="MIG",
                    severity="medium",
                    message=(
                        "Inference workloads are running on underused full GPUs; MIG partitioning can improve density."
                    ),
                    code="mig_opportunity",
                )
            )

    groups: dict[str, list[int]] = defaultdict(list)
    for g in gpus:
        groups[g["nvlink_group"]].append(g["id"])
    if len(groups) >= 2 and any(w.kind == "training" and w.gpu_demand >= train_gpu_req for w in workloads):
        findings.append(
            Finding(
                category="NVLINK",
                severity="high",
                message=(
                    "Multi-GPU training workload detected. Keeping GPUs within one NVLink group is recommended."
                ),
                code="nvlink_spread_training",
            )
        )

    if not findings:
        findings.append(
            Finding(
                category="HEALTHY",
                severity="low",
                message="No major bottlenecks detected from the provided sample telemetry.",
                code="healthy",
            )
        )

    return findings


def build_placement_recommendation(
    scenario: dict[str, Any], workloads: list[Workload], current_score: int, profile: str = "default"
) -> RecommendationResult:
    gpus = scenario["gpus"]
    cfg_map = get_profile_map("rule_thresholds")
    cfg = cfg_map.get(profile, cfg_map.get("default", {}))
    util_score_factor = float(cfg.get("expected_util_score_factor", 0.77))
    util_gain = int(cfg.get("expected_util_gain", 30))
    groups: dict[str, list[int]] = defaultdict(list)
    for g in gpus:
        groups[g["nvlink_group"]].append(g["id"])

    sorted_groups = sorted(groups.values(), key=lambda x: len(x), reverse=True)
    primary_group = sorted_groups[0] if sorted_groups else []

    items: list[PlacementItem] = []

    train_jobs = [w for w in workloads if w.kind == "training"]
    infer_jobs = [w for w in workloads if w.kind == "inference"]

    for job in sorted(train_jobs, key=lambda j: j.gpu_demand, reverse=True):
        target = primary_group[: max(1, min(job.gpu_demand, len(primary_group)))]
        items.append(
            PlacementItem(
                workload=job.name,
                action=f"Move to NVLink group GPUs {target} with NUMA-aligned CPU pinning.",
                code="move_training_nvlink",
                data={"target_gpus": target},
            )
        )

    mig_host = max(gpus, key=lambda x: (x["gpu_util"] < 50, -x["gpu_util"], x["id"]))
    for job in infer_jobs:
        items.append(
            PlacementItem(
                workload=job.name,
                action=(
                    f"Consolidate on GPU {mig_host['id']} via MIG profile 1g.20gb "
                    "for higher inference density."
                ),
                code="consolidate_inference_mig",
                data={"host_gpu": mig_host["id"], "profile": "1g.20gb"},
            )
        )

    util_before = int(round(current_score * util_score_factor))
    util_after = min(95, util_before + util_gain)

    return RecommendationResult(
        items=items,
        expected_util_before=util_before,
        expected_util_after=util_after,
        expected_training_gain_pct=35,
        expected_latency_drop_pct=20,
    )
