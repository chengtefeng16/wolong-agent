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
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from h5_delegation_config_loader_v1 import build_config

def validate_preset(config):
    policy = config.get("delegation_policy", {}) or {}
    result = {
        "delegation_master_switch": policy.get("delegation_master_switch"),
        "delegation_enabled": policy.get("delegation_enabled"),
        "delegation_stage": policy.get("delegation_stage"),
        "permission_level": policy.get("permission_level"),
        "time_control_enabled": (policy.get("time_control", {}) or {}).get("enabled"),
        "channel_control_enabled": (policy.get("channel_control", {}) or {}).get("enabled"),
        "action_control_enabled": (policy.get("action_control", {}) or {}).get("enabled"),
        "risk_control_enabled": (policy.get("risk_control", {}) or {}).get("enabled"),
        "business_stage_control_enabled": (policy.get("business_stage_control", {}) or {}).get("enabled"),
        "customer_send_enabled": (policy.get("action_control", {}) or {}).get("customer_send_enabled"),
        "customer_send_allowed_levels": (policy.get("permission_control", {}) or {}).get("customer_send_allowed_levels", []),
        "allowed_channels": policy.get("allowed_channels", []),
        "allowed_actions": policy.get("allowed_actions", []),
        "risk_levels_allowed": policy.get("risk_levels_allowed", []),
        "business_stages_allowed": policy.get("business_stages_allowed", []),
        "manual_review_required": policy.get("manual_review_required"),
        "human_supervision_mode": policy.get("human_supervision_mode"),
        "audit_required": policy.get("audit_required"),
        "rollback_enabled": policy.get("rollback_enabled"),
        "applied_preset": config.get("applied_preset"),
    }
    return result

if __name__ == "__main__":
    preset_key = sys.argv[1] if len(sys.argv) > 1 else None
    merged = build_config(preset_key=preset_key)
    validated = validate_preset(merged)
    print(json.dumps(validated, ensure_ascii=False, indent=2))
