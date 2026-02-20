from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infralens.data import Workload
from infralens.rules import RecommendationResult


@dataclass
class ExecutionConfig:
    environment: str = "bare_metal"  # bare_metal | docker
    entry_command: str = "python train.py"
    workdir: str = ""
    image_name: str = "your-image:latest"
    container_prefix: str = "infralens-job"
    extra_args: str = ""
    env_vars: dict[str, str] | None = None
    cpu_set_mode: str = "auto"  # auto | manual
    manual_cpu_set: str = ""
    gpu_visibility_style: str = "cuda_visible_devices"  # cuda_visible_devices | docker_gpus_device


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
    scenario: dict[str, Any],
    workloads: list[Workload],
    recommendation: RecommendationResult,
    exec_cfg: ExecutionConfig | None = None,
) -> list[CommandTemplate]:
    cfg = exec_cfg or ExecutionConfig()
    workload_map = {w.name: w for w in workloads}
    templates: list[CommandTemplate] = []

    def _effective_cpu_set(socket_id: int) -> str:
        if cfg.cpu_set_mode == "manual" and cfg.manual_cpu_set.strip():
            return cfg.manual_cpu_set.strip()
        return _cpu_set_for_socket(socket_id)

    def _env_prefix(extra_cuda: str | None = None) -> str:
        envs = dict(cfg.env_vars or {})
        if extra_cuda is not None and cfg.gpu_visibility_style == "cuda_visible_devices":
            envs["CUDA_VISIBLE_DEVICES"] = extra_cuda
        if not envs:
            return ""
        return " ".join([f"{k}={v}" for k, v in envs.items()]) + " "

    def _tail_args(workload_name: str) -> str:
        extra = cfg.extra_args.strip()
        return f" --workload {workload_name}" + (f" {extra}" if extra else "")

    def _docker_run_prefix(workload_name: str, gpu_csv: str, cpu_set: str) -> str:
        image = cfg.image_name.strip() or "your-image:latest"
        name = f"{cfg.container_prefix}-{workload_name}".replace("_", "-")
        wd = f" -w {cfg.workdir.strip()}" if cfg.workdir.strip() else ""
        env_flags = " ".join([f"-e {k}={v}" for k, v in (cfg.env_vars or {}).items()])
        if cfg.gpu_visibility_style == "cuda_visible_devices":
            env_flags = (env_flags + f" -e CUDA_VISIBLE_DEVICES={gpu_csv}").strip()
            gpus_flag = f'--gpus "device={gpu_csv}"'
        else:
            gpus_flag = f'--gpus "device={gpu_csv}"'
        env_block = f" {env_flags}" if env_flags else ""
        return f"docker run --rm --name {name} {gpus_flag} --cpuset-cpus=\"{cpu_set}\"{wd}{env_block} {image}"

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
            cpu_set = _effective_cpu_set(socket_id)
            cmd = cfg.entry_command.strip() or "python train.py"
            tail = _tail_args(w.name)
            env_prefix = _env_prefix(gpu_csv)

            templates.append(
                CommandTemplate(
                    workload=w.name,
                    numactl_cmd=(
                        f"{env_prefix}numactl --cpunodebind={socket_id} "
                        f"--membind={socket_id} {cmd}{tail}"
                    ),
                    taskset_cmd=(
                        f"{env_prefix}taskset -c {cpu_set} {cmd}{tail}"
                    ),
                    docker_cmd=(
                        f"{_docker_run_prefix(w.name, gpu_csv, cpu_set)} "
                        f"{cmd}{tail}"
                    ),
                )
            )
            continue

        if item.code == "consolidate_inference_mig":
            host_gpu = int((item.data or {}).get("host_gpu", 0))
            mig_profile = str((item.data or {}).get("profile", "1g.20gb"))
            socket_id = _socket_for_gpu(scenario, host_gpu)
            cpu_set = _effective_cpu_set(socket_id)
            cmd = cfg.entry_command.strip() or "python serve.py"
            tail = _tail_args(w.name)
            env_prefix = _env_prefix(str(host_gpu))

            templates.append(
                CommandTemplate(
                    workload=w.name,
                    numactl_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\n"
                        f"{env_prefix}numactl --cpunodebind={socket_id} "
                        f"--membind={socket_id} {cmd}{tail}"
                    ),
                    taskset_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\n"
                        f"{env_prefix}taskset -c {cpu_set} {cmd}{tail}"
                    ),
                    docker_cmd=(
                        f"# MIG profile: {mig_profile} on GPU {host_gpu}\n"
                        f"{_docker_run_prefix(w.name, str(host_gpu), cpu_set)} "
                        f"{cmd}{tail}"
                    ),
                )
            )

    return templates
