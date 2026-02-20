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


def _build_l4_1gpu_smb_starter() -> SampleScenario:
    return {
        "name": "SMB Starter - L4 1-GPU Inference",
        "total_vram_gb": 24,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 41,
                "vram_used_gb": 9,
                "network_io_score": 0.46,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            }
        ],
    }


def _build_l40s_2gpu_smb_growth() -> SampleScenario:
    return {
        "name": "SMB Growth - L40s 2-GPU Hybrid",
        "total_vram_gb": 48,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 63,
                "vram_used_gb": 25,
                "network_io_score": 0.58,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 1,
                "gpu_util": 34,
                "vram_used_gb": 11,
                "network_io_score": 0.43,
                "numa_node": 0,
                "cpu_socket": 1,
                "nvlink_group": "A",
            },
        ],
    }


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


def _build_l40s_4gpu_midmarket_inference() -> SampleScenario:
    return {
        "name": "Mid-Market Inference - L40s 4-GPU",
        "total_vram_gb": 48,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 79,
                "vram_used_gb": 33,
                "network_io_score": 0.76,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 1,
                "gpu_util": 71,
                "vram_used_gb": 30,
                "network_io_score": 0.72,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 2,
                "gpu_util": 56,
                "vram_used_gb": 19,
                "network_io_score": 0.61,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 3,
                "gpu_util": 47,
                "vram_used_gb": 14,
                "network_io_score": 0.55,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
        ],
    }


def _build_h100_8gpu_midmarket_training() -> SampleScenario:
    return {
        "name": "Mid-Market Training - H100 8-GPU",
        "total_vram_gb": 80,
        "gpus": [
            {
                "id": 0,
                "gpu_util": 87,
                "vram_used_gb": 63,
                "network_io_score": 0.69,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 1,
                "gpu_util": 85,
                "vram_used_gb": 60,
                "network_io_score": 0.67,
                "numa_node": 0,
                "cpu_socket": 0,
                "nvlink_group": "A",
            },
            {
                "id": 2,
                "gpu_util": 82,
                "vram_used_gb": 56,
                "network_io_score": 0.64,
                "numa_node": 0,
                "cpu_socket": 1,
                "nvlink_group": "A",
            },
            {
                "id": 3,
                "gpu_util": 79,
                "vram_used_gb": 52,
                "network_io_score": 0.63,
                "numa_node": 0,
                "cpu_socket": 1,
                "nvlink_group": "A",
            },
            {
                "id": 4,
                "gpu_util": 76,
                "vram_used_gb": 49,
                "network_io_score": 0.61,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 5,
                "gpu_util": 68,
                "vram_used_gb": 37,
                "network_io_score": 0.56,
                "numa_node": 1,
                "cpu_socket": 0,
                "nvlink_group": "B",
            },
            {
                "id": 6,
                "gpu_util": 59,
                "vram_used_gb": 27,
                "network_io_score": 0.50,
                "numa_node": 1,
                "cpu_socket": 1,
                "nvlink_group": "B",
            },
            {
                "id": 7,
                "gpu_util": 52,
                "vram_used_gb": 22,
                "network_io_score": 0.48,
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


def workloads_for_scenario(scenario_name: str) -> list[Workload]:
    if scenario_name.startswith("SMB Starter"):
        return [
            Workload(name="inference-api-01", kind="inference", gpu_demand=1, vram_gb=8),
            Workload(name="inference-batch-01", kind="inference", gpu_demand=1, vram_gb=6),
        ]
    if scenario_name.startswith("SMB Growth"):
        return [
            Workload(name="training-light-01", kind="training", gpu_demand=1, vram_gb=20),
            Workload(name="inference-api-01", kind="inference", gpu_demand=1, vram_gb=10),
            Workload(name="inference-api-02", kind="inference", gpu_demand=1, vram_gb=8),
        ]
    if scenario_name.startswith("Mid-Market Inference"):
        return [
            Workload(name="inference-api-01", kind="inference", gpu_demand=1, vram_gb=14),
            Workload(name="inference-api-02", kind="inference", gpu_demand=1, vram_gb=12),
            Workload(name="inference-batch-01", kind="inference", gpu_demand=1, vram_gb=10),
            Workload(name="training-light-01", kind="training", gpu_demand=1, vram_gb=18),
        ]
    if scenario_name.startswith("Mid-Market Training"):
        return [
            Workload(name="training-main-01", kind="training", gpu_demand=4, vram_gb=64),
            Workload(name="training-main-02", kind="training", gpu_demand=2, vram_gb=48),
            Workload(name="inference-api-01", kind="inference", gpu_demand=1, vram_gb=12),
            Workload(name="inference-api-02", kind="inference", gpu_demand=1, vram_gb=10),
        ]
    return default_workloads()


def sample_scenarios() -> dict[str, SampleScenario]:
    smb_l4 = _build_l4_1gpu_smb_starter()
    smb_l40s_2 = _build_l40s_2gpu_smb_growth()
    mid_l40s = _build_l40s_4gpu_midmarket_inference()
    mid_h100 = _build_h100_8gpu_midmarket_training()
    h200 = _build_h200_8gpu()
    l40s = _build_l40s_4gpu()
    return {
        smb_l4["name"]: smb_l4,
        smb_l40s_2["name"]: smb_l40s_2,
        mid_l40s["name"]: mid_l40s,
        mid_h100["name"]: mid_h100,
        h200["name"]: h200,
        l40s["name"]: l40s,
    }
