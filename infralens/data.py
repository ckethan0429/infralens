from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Workload:
    name: str
    kind: str  # training | inference
    gpu_demand: int
    vram_gb: int


SampleScenario = dict[str, Any]


def _build_h200_8gpu() -> SampleScenario:
    return {
        "name": "H200 8-GPU Server",
        "total_vram_gb": 141,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 92,
                "vram_used_gb": 132,
                "network_io_score": 0.71,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 1,
                "gpu_util": 90,
                "vram_used_gb": 128,
                "network_io_score": 0.69,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 2,
                "gpu_util": 88,
                "vram_used_gb": 124,
                "network_io_score": 0.65,
                "numa_node": 0,
                "cpu_socket": 1,
                "nvlink_group": "A",
            },
            {
                "id": 3,
                "gpu_util": 84,
                "vram_used_gb": 118,
                "network_io_score": 0.66,
                "numa_node": 0,
                "cpu_socket": 1,
                "nvlink_group": "A",
            },
            {
                "id": 4,
                "gpu_util": 78,
                "vram_used_gb": 110,
                "network_io_score": 0.64,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 5,
                "gpu_util": 72,
                "vram_used_gb": 100,
                "network_io_score": 0.60,
                "numa_node": 1,
                "cpu_socket": 0,
                "nvlink_group": "B",
            },
            {
                "id": 6,
                "gpu_util": 66,
                "vram_used_gb": 90,
                "network_io_score": 0.63,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 7,
                "gpu_util": 58,
                "vram_used_gb": 78,
                "network_io_score": 0.63,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
        ],
    }


def _build_l40s_4gpu() -> SampleScenario:
    return {
        "name": "L40s 4-GPU Server",
        "total_vram_gb": 48,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 74,
                "vram_used_gb": 31,
                "network_io_score": 0.70,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 1,
                "gpu_util": 68,
                "vram_used_gb": 28,
                "network_io_score": 0.66,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 2,
                "gpu_util": 43,
                "vram_used_gb": 15,
                "network_io_score": 0.52,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 3,
                "gpu_util": 36,
                "vram_used_gb": 12,
                "network_io_score": 0.47,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
        ],
    }


def default_workloads() -> list[Workload]:
    return [
        Workload(name="training-01", kind="training", gpu_demand=4, vram_gb=90),
        Workload(name="training-02", kind="training", gpu_demand=2, vram_gb=60),
        Workload(name="training-03", kind="training", gpu_demand=2, vram_gb=45),
        Workload(name="inference-01", kind="inference", gpu_demand=1, vram_gb=12),
        Workload(name="inference-02", kind="inference", gpu_demand=1, vram_gb=10),
    ]


def sample_scenarios() -> dict[str, SampleScenario]:
    h200 = _build_h200_8gpu()
    l40s = _build_l40s_4gpu()
    return {
        h200["name"]: h200,
        l40s["name"]: l40s,
    }
