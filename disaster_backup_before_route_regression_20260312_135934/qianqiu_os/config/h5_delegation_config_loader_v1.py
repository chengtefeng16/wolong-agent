# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import json
import copy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "h5_delegation_default_config_v1.json"
PRESETS_PATH = BASE_DIR / "h5_delegation_presets_v1.json"

def deep_merge(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        merged = copy.deepcopy(base)
        for k, v in override.items():
            if k in merged:
                merged[k] = deep_merge(merged[k], v)
            else:
                merged[k] = copy.deepcopy(v)
        return merged
    return copy.deepcopy(override)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_preset_map():
    presets_data = load_json(PRESETS_PATH)
    presets = presets_data.get("presets", [])
    return {item["key"]: item for item in presets if "key" in item}

def build_config(preset_key=None):
    default_data = load_json(DEFAULT_CONFIG_PATH)
    result = copy.deepcopy(default_data)

    if not preset_key:
        return result

    preset_map = get_preset_map()
    if preset_key not in preset_map:
        raise ValueError(f"preset not found: {preset_key}")

    preset = preset_map[preset_key]
    preset_policy = preset.get("delegation_policy", {})
    result["delegation_policy"] = deep_merge(
        result.get("delegation_policy", {}),
        preset_policy
    )
    result["applied_preset"] = preset_key
    return result

if __name__ == "__main__":
    import sys

    preset_key = sys.argv[1] if len(sys.argv) > 1 else None
    merged = build_config(preset_key=preset_key)
    print(json.dumps(merged, ensure_ascii=False, indent=2))
