from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infralens.data import Workload
from infralens.rules import RecommendationResult


@dataclass
class CommandTemplate:
    workload: str
    numactl_cmd: str
    taskset_cmd: str
    docker_cmd: str


def _cpu_set_for_socket(socket_id: int) -> str:
    # Generic template ranges for dual-socket hosts; adjust in production.
    return "0-23,48-71" if socket_id == 0 else "24-47,72-95"


def _socket_for_gpu(scenario: dict[str, Any], gpu_id: int) -> int:
    for g in scenario.get("gpus", []):
        if int(g.get("id", -1)) == gpu_id:
            return int(g.get("cpu_socket", g.get("numa_node", 0)))
    return 0


def build_execution_templates(
    scenario: dict[str, Any], workloads: list[Workload], recommendation: RecommendationResult
) -> list[CommandTemplate]:
    workload_map = {w.name: w for w in workloads}
    templates: list[CommandTemplate] = []

    for item in recommendation.items:
        w = workload_map.get(item.workload)
        if not w:
            continue

        if item.code == "move_training_nvlink":
            target_gpus = [int(x) for x in (item.data or {}).get("target_gpus", [])]
            if not target_gpus:
                continue
            gpu_csv = ",".join(str(g) for g in target_gpus)
            socket_id = _socket_for_gpu(scenario, target_gpus[0])
            cpu_set = _cpu_set_for_socket(socket_id)

            templates.append(
                CommandTemplate(
                    workload=w.name,
                    numactl_cmd=(
                        f"CUDA_VISIBLE_DEVICES={gpu_csv} numactl --cpunodebind={socket_id} "
                        f"--membind={socket_id} python train.py --workload {w.name}"
                    ),
                    taskset_cmd=(
                        f"CUDA_VISIBLE_DEVICES={gpu_csv} taskset -c {cpu_set} "
                        f"python train.py --workload {w.name}"
                    ),
                    docker_cmd=(
                        f"docker run --rm --gpus '\"device={gpu_csv}\"' --cpuset-cpus=\"{cpu_set}\" "
                        f"-e CUDA_VISIBLE_DEVICES={gpu_csv} your-image:latest "
                        f"python train.py --workload {w.name}"
                    ),
                )
            )
            continue

        if item.code == "consolidate_inference_mig":
            host_gpu = int((item.data or {}).get("host_gpu", 0))
            mig_profile = str((item.data or {}).get("profile", "1g.20gb"))
            socket_id = _socket_for_gpu(scenario, host_gpu)
            cpu_set = _cpu_set_for_socket(socket_id)

            templates.append(
                CommandTemplate(
                    workload=w.name,
                    numactl_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\\n"
                        f"CUDA_VISIBLE_DEVICES={host_gpu} numactl --cpunodebind={socket_id} "
                        f"--membind={socket_id} python serve.py --workload {w.name}"
                    ),
                    taskset_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\\n"
                        f"CUDA_VISIBLE_DEVICES={host_gpu} taskset -c {cpu_set} "
                        f"python serve.py --workload {w.name}"
                    ),
                    docker_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\\n"
                        f"docker run --rm --gpus '\"device={host_gpu}\"' --cpuset-cpus=\"{cpu_set}\" "
                        f"-e CUDA_VISIBLE_DEVICES={host_gpu} your-image:latest "
                        f"python serve.py --workload {w.name}"
                    ),
                )
            )

    return templates
