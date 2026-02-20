from __future__ import annotations

import csv
import json
import re
from io import StringIO
from typing import Any

import pandas as pd


def _normalize_col(col: str) -> str:
    col = col.strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", col).strip("_")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    text = re.sub(r"[^0-9.\-]+", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _pick_value(row: dict[str, Any], keys: list[str], default: Any) -> Any:
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
    return default


def _looks_like_header(row: list[str]) -> bool:
    def _is_numberish(cell: str) -> bool:
        return bool(re.fullmatch(r"[+\-]?\d+(\.\d+)?", cell.strip()))

    headerish_count = 0
    for cell in row:
        token = cell.strip()
        if not token:
            continue
        if re.search(r"[a-zA-Z_.]", token) and not _is_numberish(token):
            headerish_count += 1

    threshold = max(2, len(row) // 2)
    return headerish_count >= threshold


def _csv_noheader_columns(col_count: int) -> list[str]:
    if col_count == 4:
        return ["index", "utilization_gpu", "memory_used", "memory_total"]
    if col_count == 5:
        return ["index", "utilization_gpu", "memory_used", "memory_total", "numa_node"]
    if col_count == 6:
        return ["index", "utilization_gpu", "memory_used", "memory_total", "numa_node", "cpu_socket"]
    if col_count >= 7:
        return [
            "index",
            "utilization_gpu",
            "memory_used",
            "memory_total",
            "numa_node",
            "cpu_socket",
            "nvlink_group",
        ] + [f"extra_{i}" for i in range(8, col_count + 1)]
    return [f"col_{i}" for i in range(1, col_count + 1)]


def _parse_csv_rows(text: str) -> list[dict[str, Any]]:
    raw_rows = [row for row in csv.reader(StringIO(text)) if any(c.strip() for c in row)]
    if not raw_rows:
        raise ValueError("Uploaded CSV is empty.")

    first = [c.strip() for c in raw_rows[0]]
    if _looks_like_header(first):
        csv_df = pd.read_csv(StringIO(text))
        csv_df.columns = [_normalize_col(c) for c in csv_df.columns]
        return csv_df.to_dict(orient="records")

    columns = _csv_noheader_columns(len(first))
    parsed_rows: list[dict[str, Any]] = []
    for row in raw_rows:
        normalized = [c.strip() for c in row]
        if len(normalized) < len(columns):
            normalized += [""] * (len(columns) - len(normalized))
        parsed_rows.append(dict(zip(columns, normalized)))
    return parsed_rows


def _build_scenario_from_rows(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    if not rows:
        raise ValueError("No GPU rows detected in uploaded file.")

    gpus: list[dict[str, Any]] = []
    memory_totals: list[float] = []

    for idx, row in enumerate(rows):
        gpu_id = int(_to_float(_pick_value(row, ["index", "gpu", "gpu_id", "id"], idx)) or idx)

        gpu_util = _to_float(
            _pick_value(
                row,
                ["utilization_gpu", "gpu_util", "gpu_utilization", "util"],
                None,
            )
        )
        mem_used_mib = _to_float(
            _pick_value(
                row,
                ["memory_used", "memory_used_mib", "fb_memory_usage_used", "vram_used_mib"],
                None,
            )
        )
        mem_total_mib = _to_float(
            _pick_value(
                row,
                ["memory_total", "memory_total_mib", "fb_memory_usage_total", "vram_total_mib"],
                None,
            )
        )

        # Allow direct GB fields if MiB fields are absent.
        mem_used_gb_raw = _to_float(_pick_value(row, ["vram_used_gb", "memory_used_gb"], None))
        mem_total_gb_raw = _to_float(_pick_value(row, ["vram_total_gb", "memory_total_gb"], None))

        vram_used_gb = mem_used_gb_raw if mem_used_gb_raw is not None else (mem_used_mib or 0.0) / 1024.0
        vram_total_gb = mem_total_gb_raw if mem_total_gb_raw is not None else (mem_total_mib or 80.0) / 1024.0

        if gpu_util is None:
            gpu_util = 0.0

        network_io_score = _to_float(_pick_value(row, ["network_io_score", "network_score"], None))
        if network_io_score is None:
            # Conservative proxy when network telemetry is missing.
            network_io_score = min(1.0, max(0.2, (gpu_util / 100.0) * 0.8 + 0.2))

        numa_node = int(_to_float(_pick_value(row, ["numa_node", "numa"], gpu_id % 2)) or (gpu_id % 2))
        cpu_socket = int(
            _to_float(_pick_value(row, ["cpu_socket", "socket", "cpu_affinity_socket"], numa_node)) or numa_node
        )
        nvlink_group = str(_pick_value(row, ["nvlink_group", "nvlink", "topology_group"], "A"))
        if nvlink_group == "A" and "nvlink_group" not in row and "nvlink" not in row:
            nvlink_group = "A" if gpu_id < max(1, len(rows) // 2) else "B"

        gpus.append(
            {
                "id": gpu_id,
                "gpu_util": round(gpu_util, 2),
                "vram_used_gb": round(vram_used_gb, 2),
                "network_io_score": round(float(network_io_score), 2),
                "numa_node": numa_node,
                "cpu_socket": cpu_socket,
                "nvlink_group": nvlink_group,
            }
        )
        memory_totals.append(vram_total_gb)

    total_vram_gb = max(1, int(round(max(memory_totals) if memory_totals else 80)))
    return {"name": name, "total_vram_gb": total_vram_gb, "gpus": gpus}


def _parse_cpu_affinity_to_set(text: str) -> set[int]:
    cpus: set[int] = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            try:
                start, end = token.split("-", 1)
                cpus.update(range(int(start), int(end) + 1))
            except ValueError:
                continue
        else:
            try:
                cpus.add(int(token))
            except ValueError:
                continue
    return cpus


def parse_numactl_hardware(text: str) -> dict[int, set[int]]:
    node_cpus: dict[int, set[int]] = {}
    for line in text.splitlines():
        m = re.match(r"\s*node\s+(\d+)\s+cpus:\s+(.+)", line.strip(), flags=re.IGNORECASE)
        if not m:
            continue
        node_id = int(m.group(1))
        cpu_list = [c for c in m.group(2).strip().split() if c]
        parsed = set()
        for c in cpu_list:
            try:
                parsed.add(int(c))
            except ValueError:
                pass
        if parsed:
            node_cpus[node_id] = parsed
    return node_cpus


def parse_numactl_hardware_any(text: str) -> dict[int, set[int]]:
    stripped = text.strip()
    if not stripped:
        return {}

    try:
        parsed = json.loads(stripped)
        node_cpus: dict[int, set[int]] = {}
        if isinstance(parsed, dict) and "nodes" in parsed and isinstance(parsed["nodes"], list):
            rows = parsed["nodes"]
        elif isinstance(parsed, list):
            rows = parsed
        elif isinstance(parsed, dict):
            rows = [{"node_id": k, "cpus": v} for k, v in parsed.items()]
        else:
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            node_id_raw = _pick_value(row, ["node_id", "node", "id"], None)
            node_id_val = _to_float(node_id_raw)
            if node_id_val is None:
                continue
            cpus_val = _pick_value(row, ["cpus", "cpu_list"], "")
            if isinstance(cpus_val, list):
                cpu_set = {int(x) for x in cpus_val if _to_float(x) is not None}
            else:
                cpu_set = _parse_cpu_affinity_to_set(str(cpus_val).replace(" ", ","))
            if cpu_set:
                node_cpus[int(node_id_val)] = cpu_set
        if node_cpus:
            return node_cpus
    except json.JSONDecodeError:
        pass

    if "," in stripped:
        try:
            df = pd.read_csv(StringIO(stripped))
            df.columns = [_normalize_col(c) for c in df.columns]
            node_cpus: dict[int, set[int]] = {}
            for row in df.to_dict(orient="records"):
                node_id_val = _to_float(_pick_value(row, ["node_id", "node", "id"], None))
                if node_id_val is None:
                    continue
                cpus_val = _pick_value(row, ["cpus", "cpu_list"], "")
                cpu_set = _parse_cpu_affinity_to_set(str(cpus_val).replace(" ", ","))
                if cpu_set:
                    node_cpus[int(node_id_val)] = cpu_set
            if node_cpus:
                return node_cpus
        except Exception:
            pass

    return parse_numactl_hardware(text)


def _derive_cpu_socket_from_affinity(affinity: str, node_cpus: dict[int, set[int]]) -> int | None:
    affinity_set = _parse_cpu_affinity_to_set(affinity)
    if not affinity_set or not node_cpus:
        return None
    best_node = None
    best_overlap = -1
    for node_id, cpus in node_cpus.items():
        overlap = len(affinity_set.intersection(cpus))
        if overlap > best_overlap:
            best_overlap = overlap
            best_node = node_id
    return best_node


def parse_nvidia_smi_topology(
    text: str, node_cpus: dict[int, set[int]] | None = None
) -> dict[int, dict[str, Any]]:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    header_idx = -1
    gpu_header: list[str] = []
    for i, line in enumerate(lines):
        if "CPU Affinity" in line and "GPU" in line:
            parts = re.split(r"\s{2,}", line.strip())
            gpu_header = [p for p in parts if p.startswith("GPU")]
            header_idx = i
            break
    if header_idx < 0 or not gpu_header:
        return {}

    node_cpus = node_cpus or {}
    infos: dict[int, dict[str, Any]] = {}
    nvlink_edges: set[tuple[int, int]] = set()

    for line in lines[header_idx + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("GPU"):
            continue
        cols = re.split(r"\s{2,}", stripped)
        if len(cols) < len(gpu_header) + 1:
            continue
        row_name = cols[0]
        try:
            src = int(row_name.replace("GPU", ""))
        except ValueError:
            continue
        matrix_cells = cols[1 : 1 + len(gpu_header)]
        extras = cols[1 + len(gpu_header) :]
        cpu_affinity = extras[0] if extras else ""
        numa_affinity = extras[1] if len(extras) > 1 else ""
        numa_node = int(numa_affinity) if str(numa_affinity).isdigit() else src % 2
        cpu_socket = _derive_cpu_socket_from_affinity(cpu_affinity, node_cpus)
        if cpu_socket is None:
            cpu_socket = numa_node

        for idx, rel in enumerate(matrix_cells):
            if idx == src:
                continue
            rel_u = rel.upper()
            if rel_u.startswith("NV"):
                a, b = sorted((src, idx))
                nvlink_edges.add((a, b))

        infos[src] = {
            "numa_node": numa_node,
            "cpu_socket": cpu_socket,
            "cpu_affinity": cpu_affinity,
        }

    # Connected components from NVLink edges -> group labels A, B, C...
    parent: dict[int, int] = {gpu_id: gpu_id for gpu_id in infos}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in nvlink_edges:
        if a in parent and b in parent:
            union(a, b)

    comp_to_gpus: dict[int, list[int]] = {}
    for gpu_id in infos:
        root = find(gpu_id)
        comp_to_gpus.setdefault(root, []).append(gpu_id)
    ordered = sorted((sorted(v) for v in comp_to_gpus.values()), key=lambda x: x[0] if x else 0)
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    gpu_to_group: dict[int, str] = {}
    for idx, comp in enumerate(ordered):
        label = labels[idx] if idx < len(labels) else f"G{idx+1}"
        for gpu_id in comp:
            gpu_to_group[gpu_id] = label

    for gpu_id, info in infos.items():
        info["nvlink_group"] = gpu_to_group.get(gpu_id, "A")

    return infos


def parse_nvidia_smi_topology_any(
    text: str, node_cpus: dict[int, set[int]] | None = None
) -> dict[int, dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return {}

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and "gpus" in parsed and isinstance(parsed["gpus"], list):
            rows = parsed["gpus"]
        elif isinstance(parsed, list):
            rows = parsed
        else:
            rows = []
        infos: dict[int, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            gpu_id_val = _to_float(_pick_value(row, ["gpu_id", "index", "id"], None))
            if gpu_id_val is None:
                continue
            gpu_id = int(gpu_id_val)
            numa_node = int(_to_float(_pick_value(row, ["numa_node", "numa_affinity"], gpu_id % 2)) or (gpu_id % 2))
            cpu_socket = int(_to_float(_pick_value(row, ["cpu_socket", "socket"], numa_node)) or numa_node)
            nvlink_group = str(_pick_value(row, ["nvlink_group", "group"], "A"))
            info: dict[str, Any] = {
                "numa_node": numa_node,
                "cpu_socket": cpu_socket,
                "nvlink_group": nvlink_group,
            }
            cpu_aff = _pick_value(row, ["cpu_affinity"], None)
            if cpu_aff is not None:
                info["cpu_affinity"] = str(cpu_aff)
            infos[gpu_id] = info
        if infos:
            return infos
    except json.JSONDecodeError:
        pass

    if "," in stripped:
        try:
            df = pd.read_csv(StringIO(stripped))
            df.columns = [_normalize_col(c) for c in df.columns]
            infos: dict[int, dict[str, Any]] = {}
            for row in df.to_dict(orient="records"):
                gpu_id_val = _to_float(_pick_value(row, ["gpu_id", "index", "id"], None))
                if gpu_id_val is None:
                    continue
                gpu_id = int(gpu_id_val)
                numa_node = int(_to_float(_pick_value(row, ["numa_node", "numa_affinity"], gpu_id % 2)) or (gpu_id % 2))
                cpu_socket = int(_to_float(_pick_value(row, ["cpu_socket", "socket"], numa_node)) or numa_node)
                nvlink_group = str(_pick_value(row, ["nvlink_group", "group"], "A"))
                info: dict[str, Any] = {
                    "numa_node": numa_node,
                    "cpu_socket": cpu_socket,
                    "nvlink_group": nvlink_group,
                }
                cpu_aff = _pick_value(row, ["cpu_affinity"], None)
                if cpu_aff is not None:
                    info["cpu_affinity"] = str(cpu_aff)
                infos[gpu_id] = info
            if infos:
                return infos
        except Exception:
            pass

    return parse_nvidia_smi_topology(text, node_cpus=node_cpus)


def apply_topology_overrides(
    scenario: dict[str, Any], topo_info: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    if not topo_info:
        return scenario
    patched = dict(scenario)
    patched_gpus: list[dict[str, Any]] = []
    for g in scenario["gpus"]:
        ng = dict(g)
        override = topo_info.get(g["id"])
        if override:
            ng["numa_node"] = int(override.get("numa_node", ng["numa_node"]))
            ng["cpu_socket"] = int(override.get("cpu_socket", ng["cpu_socket"]))
            ng["nvlink_group"] = str(override.get("nvlink_group", ng["nvlink_group"]))
        patched_gpus.append(ng)
    patched["gpus"] = patched_gpus
    return patched


def parse_uploaded_telemetry(
    filename: str,
    raw_bytes: bytes,
    topo_text: str | None = None,
    numactl_text: str | None = None,
) -> dict[str, Any]:
    text = raw_bytes.decode("utf-8", errors="ignore").strip()
    if not text:
        raise ValueError("Uploaded file is empty.")

    lower_name = filename.lower()
    if lower_name.endswith(".json"):
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "gpus" in parsed:
            rows = parsed["gpus"]
        elif isinstance(parsed, dict) and "gpu" in parsed:
            rows = parsed["gpu"]
        elif isinstance(parsed, list):
            rows = parsed
        else:
            raise ValueError("Unsupported JSON structure. Expected list or {gpus:[...]} format.")
        if not isinstance(rows, list):
            raise ValueError("JSON GPU payload must be a list.")
        normalized_rows = [{_normalize_col(k): v for k, v in row.items()} for row in rows if isinstance(row, dict)]
        scenario = _build_scenario_from_rows(normalized_rows, f"Uploaded ({filename})")
    else:
        rows = _parse_csv_rows(text)
        rows = [{_normalize_col(k): v for k, v in row.items()} for row in rows]
        scenario = _build_scenario_from_rows(rows, f"Uploaded ({filename})")

    if topo_text:
        node_cpus = parse_numactl_hardware_any(numactl_text or "")
        topo_info = parse_nvidia_smi_topology_any(topo_text, node_cpus=node_cpus)
        scenario = apply_topology_overrides(scenario, topo_info)

    return scenario
