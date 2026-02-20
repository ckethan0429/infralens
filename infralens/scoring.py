from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from infralens.config import get_profile_map
from infralens.data import Workload


@dataclass
class ScoreResult:
    score: int
    grade: str
    gpu_score: float
    numa_score: float
    network_score: float
    profile: str


def _gpu_component(gpu_util: float, vram_used: float, vram_total: float) -> float:
    return (gpu_util / 100.0) * 0.4 + (vram_used / vram_total) * 0.3


def _numa_component(numa_node: int, cpu_socket: int) -> float:
    return 1.0 if numa_node == cpu_socket else 0.5


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def infer_workload_profile(workloads: list[Workload]) -> str:
    if not workloads:
        return "default"
    train_gpu = sum(w.gpu_demand for w in workloads if w.kind == "training")
    infer_gpu = sum(w.gpu_demand for w in workloads if w.kind == "inference")
    if train_gpu == infer_gpu:
        return "default"
    return "training" if train_gpu > infer_gpu else "inference"


def calculate_efficiency_score(
    scenario: dict[str, Any], profile: str = "default"
) -> ScoreResult:
    gpus = scenario["gpus"]
    vram_total = float(scenario["total_vram_gb"])
    weights = get_profile_map("score_weights")
    w = weights.get(profile, weights.get("default", {"gpu": 0.6, "numa": 0.2, "network": 0.2}))

    gpu_components = [
        _gpu_component(g["gpu_util"], g["vram_used_gb"], vram_total) for g in gpus
    ]
    numa_components = [_numa_component(g["numa_node"], g["cpu_socket"]) for g in gpus]
    network_components = [float(g["network_io_score"]) for g in gpus]

    gpu_score = mean(gpu_components)
    numa_score = mean(numa_components)
    network_score = mean(network_components)

    total = (
        gpu_score * float(w["gpu"])
        + numa_score * float(w["numa"])
        + network_score * float(w["network"])
    )
    score = round(total * 100)
    return ScoreResult(
        score=score,
        grade=grade_from_score(score),
        gpu_score=gpu_score,
        numa_score=numa_score,
        network_score=network_score,
        profile=profile,
    )
