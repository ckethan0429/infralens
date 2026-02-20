from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from infralens.data import sample_scenarios, workloads_for_scenario
from infralens.rules import build_placement_recommendation, detect_bottlenecks
from infralens.scoring import calculate_efficiency_score, infer_workload_profile


@dataclass
class TestSummary:
    total: int
    passed: int
    pass_rate: float
    return_code: int


def _parse_test_summary(output: str, return_code: int) -> TestSummary:
    ran_match = re.search(r"Ran\s+(\d+)\s+tests?", output)
    total = int(ran_match.group(1)) if ran_match else 0
    if return_code == 0:
        passed = total
    else:
        fail_match = re.search(r"failures=(\d+)", output)
        err_match = re.search(r"errors=(\d+)", output)
        failures = int(fail_match.group(1)) if fail_match else 0
        errors = int(err_match.group(1)) if err_match else 0
        passed = max(0, total - failures - errors)
    pass_rate = (passed / total) if total else 0.0
    return TestSummary(total=total, passed=passed, pass_rate=pass_rate, return_code=return_code)


def measure_test_pass_rate() -> TestSummary:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join([proc.stdout, proc.stderr]).strip()
    return _parse_test_summary(output, proc.returncode)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = min(len(sorted_vals) - 1, int(0.95 * (len(sorted_vals) - 1)))
    return sorted_vals[idx]


def measure_response_and_recommendation(iterations: int) -> dict:
    scenarios = sample_scenarios()
    score_times: list[float] = []
    pipeline_times: list[float] = []
    recommendation_attempts = 0
    bottleneck_scenarios = 0
    recommended_scenarios = 0
    consistency_successes = 0

    for _ in range(iterations):
        for name, scenario in scenarios.items():
            workloads = workloads_for_scenario(name)
            profile = infer_workload_profile(workloads)

            t0 = time.perf_counter()
            score = calculate_efficiency_score(scenario, profile=profile)
            score_times.append(time.perf_counter() - t0)

            t1 = time.perf_counter()
            findings = detect_bottlenecks(scenario, workloads, profile=profile)
            rec = build_placement_recommendation(scenario, workloads, score.score, profile=profile)
            pipeline_times.append(time.perf_counter() - t1)

            recommendation_attempts += 1
            has_bottleneck = len(findings) > 0
            has_recommendation = len(rec.items) > 0
            if has_bottleneck:
                bottleneck_scenarios += 1
            if has_recommendation:
                recommended_scenarios += 1
            # Consistent if:
            # - bottleneck exists and recommendation exists
            # - no bottleneck and no recommendation
            if (has_bottleneck and has_recommendation) or ((not has_bottleneck) and (not has_recommendation)):
                consistency_successes += 1

    return {
        "response_time_sec": {
            "score_avg": round(statistics.mean(score_times), 6) if score_times else 0.0,
            "score_p95": round(_p95(score_times), 6),
            "analysis_pipeline_avg": round(statistics.mean(pipeline_times), 6) if pipeline_times else 0.0,
            "analysis_pipeline_p95": round(_p95(pipeline_times), 6),
        },
        "recommendation_consistency": {
            "attempts": recommendation_attempts,
            "bottleneck_scenarios": bottleneck_scenarios,
            "no_bottleneck_scenarios": recommendation_attempts - bottleneck_scenarios,
            "recommended_scenarios": recommended_scenarios,
            "consistency_successes": consistency_successes,
            "consistency_rate": round((consistency_successes / recommendation_attempts) if recommendation_attempts else 0.0, 6),
        },
    }


def collect_success_metrics(
    *,
    iterations: int = 3,
    out_path: str = "logs/success_metrics.jsonl",
    phase: str = "",
) -> tuple[dict, Path]:
    iters = max(1, int(iterations))
    test_summary = measure_test_pass_rate()
    runtime_summary = measure_response_and_recommendation(iterations=iters)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase.strip() if phase else "",
        "iterations": iters,
        "methodology": {
            "test_command": "python -m unittest discover -s tests -p 'test_*.py'",
            "test_pass_rate_formula": "passed_tests / total_tests",
            "recommendation_consistency_formula": "consistency_successes / attempted_scenarios",
            "recommendation_consistency_definition": (
                "Consistent when bottleneck exists and recommendation exists, "
                "or no bottleneck and no recommendation."
            ),
        },
        "targets": {
            "score_response_time_sec_max": 1.0,
            "llm_response_time_sec_max": 10.0,
            "analysis_accuracy_target": "NUMA/NVLink issue detection in test scenarios",
        },
        "test_pass_rate": asdict(test_summary),
        **runtime_summary,
    }

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record, output


def load_recent_metrics(out_path: str, limit: int = 20) -> list[dict]:
    path = Path(out_path)
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            token = line.strip()
            if not token:
                continue
            try:
                rows.append(json.loads(token))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]
