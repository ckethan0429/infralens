from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "score_weights": {
        "default": {"gpu": 0.6, "numa": 0.2, "network": 0.2},
        "training": {"gpu": 0.65, "numa": 0.25, "network": 0.1},
        "inference": {"gpu": 0.55, "numa": 0.15, "network": 0.3},
    },
    "rule_thresholds": {
        "default": {
            "low_util_threshold": 45,
            "low_util_fraction": 0.25,
            "mig_underused_util_threshold": 65,
            "mig_underused_vram_threshold_gb": 90,
            "requires_training_gpus": 4,
            "expected_util_score_factor": 0.77,
            "expected_util_gain": 30,
        },
        "training": {
            "low_util_threshold": 50,
            "low_util_fraction": 0.25,
            "mig_underused_util_threshold": 60,
            "mig_underused_vram_threshold_gb": 80,
            "requires_training_gpus": 4,
            "expected_util_score_factor": 0.78,
            "expected_util_gain": 28,
        },
        "inference": {
            "low_util_threshold": 40,
            "low_util_fraction": 0.33,
            "mig_underused_util_threshold": 70,
            "mig_underused_vram_threshold_gb": 60,
            "requires_training_gpus": 4,
            "expected_util_score_factor": 0.75,
            "expected_util_gain": 32,
        },
    },
}


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parent.parent / "config" / "optimization_profiles.json"
    if not config_path.exists():
        return DEFAULT_CONFIG
    try:
        with config_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
    return DEFAULT_CONFIG


def get_profile_map(section: str) -> dict[str, dict[str, Any]]:
    cfg = load_config()
    section_map = cfg.get(section, {})
    if not isinstance(section_map, dict):
        return DEFAULT_CONFIG.get(section, {})
    merged = dict(DEFAULT_CONFIG.get(section, {}))
    merged.update(section_map)
    return merged
