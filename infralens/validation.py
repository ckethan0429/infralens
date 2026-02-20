from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationResult:
    env_vars: dict[str, str]
    invalid_env_lines: list[int]
    errors: list[str]


def parse_env_vars(raw: str) -> tuple[dict[str, str], list[int]]:
    out: dict[str, str] = {}
    invalid_lines: list[int] = []
    for idx, line in enumerate(raw.splitlines(), 1):
        token = line.strip()
        if not token:
            continue
        if "=" not in token:
            invalid_lines.append(idx)
            continue
        key, value = token.split("=", 1)
        k = key.strip()
        if k:
            out[k] = value.strip()
        else:
            invalid_lines.append(idx)
    return out, invalid_lines


def validate_execution_settings(
    *,
    exec_env_ui: str,
    exec_entry: str,
    exec_image: str,
    exec_cpumode_ui: str,
    exec_cpumanual: str,
    exec_envvars_raw: str,
) -> ValidationResult:
    env_vars, invalid_lines = parse_env_vars(exec_envvars_raw)
    errors: list[str] = []

    if not exec_entry.strip():
        errors.append("Entry command is required.")
    if exec_env_ui == "Docker" and not exec_image.strip():
        errors.append("Docker image is required in Docker mode.")
    if exec_cpumode_ui == "Manual" and not exec_cpumanual.strip():
        errors.append("Manual CPU set is required in Manual mode.")
    if invalid_lines:
        line_str = ",".join(str(i) for i in invalid_lines)
        errors.append(f"Invalid env var line(s): {line_str}")

    return ValidationResult(env_vars=env_vars, invalid_env_lines=invalid_lines, errors=errors)

