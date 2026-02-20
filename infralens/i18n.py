from __future__ import annotations

from infralens.rules import Finding, PlacementItem, RecommendationResult


def _lang(language: str) -> str:
    l = language.lower()
    if l.startswith("zh"):
        return "zh"
    if l.startswith("en"):
        return "en"
    return "ko"


def localize_category(category: str, language: str) -> str:
    m = {
        "ko": {"NUMA": "NUMA", "GPU_UTIL": "GPU 활용률", "MIG": "MIG", "NVLINK": "NVLink", "HEALTHY": "상태"},
        "en": {"NUMA": "NUMA", "GPU_UTIL": "GPU Utilization", "MIG": "MIG", "NVLINK": "NVLink", "HEALTHY": "Health"},
        "zh": {"NUMA": "NUMA", "GPU_UTIL": "GPU 利用率", "MIG": "MIG", "NVLINK": "NVLink", "HEALTHY": "状态"},
    }
    l = _lang(language)
    return m[l].get(category, category)


def localize_severity(severity: str, language: str) -> str:
    m = {
        "ko": {"high": "높음", "medium": "중간", "low": "낮음"},
        "en": {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"},
        "zh": {"high": "高", "medium": "中", "low": "低"},
    }
    l = _lang(language)
    return m[l].get(severity, severity)


def localize_finding_message(finding: Finding, language: str) -> str:
    l = _lang(language)
    d = finding.data or {}

    if finding.code == "numa_mismatch":
        if l == "ko":
            return f"GPU {d.get('gpu_id')}는 NUMA 불일치 상태입니다 (GPU NUMA {d.get('numa_node')} / CPU 소켓 {d.get('cpu_socket')})."
        if l == "zh":
            return f"GPU {d.get('gpu_id')} 存在 NUMA 不匹配（GPU NUMA {d.get('numa_node')} / CPU Socket {d.get('cpu_socket')}）。"
        return f"GPU {d.get('gpu_id')} has NUMA mismatch (GPU NUMA {d.get('numa_node')} vs CPU socket {d.get('cpu_socket')})."

    if finding.code == "low_gpu_util":
        if l == "ko":
            return f"{d.get('count')}개 GPU가 낮은 활용률(<{d.get('threshold')}%)을 보이며 리소스 과소할당 가능성이 있습니다."
        if l == "zh":
            return f"{d.get('count')} 张 GPU 利用率较低（<{d.get('threshold')}%），可能存在资源欠分配。"
        return f"{d.get('count')} GPU(s) show low utilization (<{d.get('threshold')}%), indicating potential under-allocation."

    if finding.code == "mig_opportunity":
        util_th = d.get("gpu_util_threshold")
        vram_th = d.get("vram_used_threshold_gb")
        if util_th is None:
            util_th = 65
        if vram_th is None:
            vram_th = 90
        vram_text = f"{vram_th:g}"
        if l == "ko":
            return (
                "추론 워크로드가 저활용 전체 GPU에서 실행 중입니다 "
                f"(기준: GPU 활용률 <{util_th}%, VRAM 사용량 <{vram_text}GB). "
                "MIG 분할로 밀도를 높일 수 있습니다."
            )
        if l == "zh":
            return (
                "推理负载正在低利用率整卡上运行"
                f"（阈值：GPU 利用率 <{util_th}% 且显存使用量 <{vram_text}GB）。"
                "可通过 MIG 切分提升密度。"
            )
        return (
            "Inference workloads are running on underused full GPUs "
            f"(thresholds: GPU utilization <{util_th}% and VRAM used <{vram_text}GB); "
            "MIG partitioning can improve density."
        )

    if finding.code == "nvlink_spread_training":
        if l == "ko":
            return "멀티 GPU 학습 워크로드가 감지되었습니다. 하나의 NVLink 그룹 내 배치를 권장합니다."
        if l == "zh":
            return "检测到多 GPU 训练任务，建议尽量在同一 NVLink 组内部署。"
        return "Multi-GPU training workload detected. Keeping GPUs within one NVLink group is recommended."

    if finding.code == "healthy":
        if l == "ko":
            return "제공된 텔레메트리 기준으로 주요 병목/비효율은 감지되지 않았습니다."
        if l == "zh":
            return "基于当前遥测数据，未检测到明显瓶颈/低效。"
        return "No major bottlenecks/inefficiencies detected from the provided sample telemetry."

    return finding.message


def localize_placement_action(item: PlacementItem, language: str) -> str:
    l = _lang(language)
    d = item.data or {}

    if item.code == "move_training_nvlink":
        target = d.get("target_gpus", [])
        if l == "ko":
            return f"NVLink 그룹 GPU {target}로 이동하고 CPU 핀닝을 NUMA 정합으로 맞추세요."
        if l == "zh":
            return f"迁移到 NVLink 组 GPU {target}，并将 CPU 绑核调整为 NUMA 对齐。"
        return f"Move to NVLink group GPUs {target} with NUMA-aligned CPU pinning."

    if item.code == "consolidate_inference_mig":
        host = d.get("host_gpu")
        profile = d.get("profile", "1g.20gb")
        if l == "ko":
            return f"추론 워크로드를 GPU {host}에 {profile} MIG 프로파일로 통합 배치하세요."
        if l == "zh":
            return f"将推理负载整合到 GPU {host}，使用 {profile} MIG 配置。"
        return f"Consolidate on GPU {host} via MIG profile {profile} for higher inference density."

    return item.action


def localize_findings(findings: list[Finding], language: str) -> list[Finding]:
    return [
        Finding(
            category=localize_category(f.category, language),
            severity=f.severity,
            message=localize_finding_message(f, language),
            code=f.code,
            data=f.data,
        )
        for f in findings
    ]


def localize_recommendation(rec: RecommendationResult, language: str) -> RecommendationResult:
    items = [
        PlacementItem(
            workload=item.workload,
            action=localize_placement_action(item, language),
            code=item.code,
            data=item.data,
        )
        for item in rec.items
    ]
    return RecommendationResult(
        items=items,
        expected_util_before=rec.expected_util_before,
        expected_util_after=rec.expected_util_after,
        expected_training_gain_pct=rec.expected_training_gain_pct,
        expected_latency_drop_pct=rec.expected_latency_drop_pct,
    )
