#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infralens.metrics import collect_success_metrics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect InfraLens success metrics (response time, test pass rate, recommendation consistency rate)."
    )
    parser.add_argument("--iterations", type=int, default=3, help="Number of repeated scenario passes.")
    parser.add_argument("--out", type=str, default="logs/success_metrics.jsonl", help="Output JSONL log path.")
    parser.add_argument("--phase", type=str, default="", help="Optional phase label (before/after).")
    args = parser.parse_args()

    record, _ = collect_success_metrics(iterations=args.iterations, out_path=args.out, phase=args.phase)
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
