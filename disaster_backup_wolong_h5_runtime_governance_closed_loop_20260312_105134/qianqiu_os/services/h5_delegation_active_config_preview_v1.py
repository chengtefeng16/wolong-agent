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
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"

def build_preview(data):
    data = data or {}
    policy = data.get("delegation_policy", {}) or {}

    preview = {
        "config_name": data.get("config_name"),
        "config_version": data.get("config_version"),
        "saved_at": data.get("saved_at"),
        "operator_id": data.get("operator_id"),
        "operator_name": data.get("operator_name"),
        "change_reason": data.get("change_reason"),
        "applied_preset": data.get("applied_preset"),

        "delegation_master_switch": policy.get("delegation_master_switch"),
        "delegation_enabled": policy.get("delegation_enabled"),
        "delegation_stage": policy.get("delegation_stage"),
        "permission_level": policy.get("permission_level"),

        "allowed_time_windows": policy.get("allowed_time_windows", []),
        "allowed_channels": policy.get("allowed_channels", []),
        "allowed_actions": policy.get("allowed_actions", []),
        "risk_levels_allowed": policy.get("risk_levels_allowed", []),
        "business_stages_allowed": policy.get("business_stages_allowed", []),

        "manual_review_required": policy.get("manual_review_required"),
        "human_supervision_mode": policy.get("human_supervision_mode"),
        "audit_required": policy.get("audit_required"),
        "rollback_enabled": policy.get("rollback_enabled"),
    }
    return preview

def main():
    if not ACTIVE_CONFIG_PATH.exists():
        print(json.dumps({
            "success": False,
            "message": "active config not found",
            "path": str(ACTIVE_CONFIG_PATH)
        }, ensure_ascii=False, indent=2))
        return

    with open(ACTIVE_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    preview = build_preview(data)
    print(json.dumps(preview, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
