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
    delegation_policy = data.get("delegation_policy", {}) or {}
    whatsapp_control = data.get("whatsapp_control", {}) or {}

    return {
        "config_name": data.get("config_name"),
        "config_version": data.get("config_version"),
        "saved_at": data.get("saved_at"),
        "operator_id": data.get("operator_id"),
        "operator_name": data.get("operator_name"),
        "change_reason": data.get("change_reason"),
        "applied_preset": data.get("applied_preset"),
        "delegation_policy": delegation_policy,
        "whatsapp_control": whatsapp_control,
    }


if __name__ == "__main__":
    if not ACTIVE_CONFIG_PATH.exists():
        print(json.dumps({
            "success": False,
            "message": "active config not found",
            "path": str(ACTIVE_CONFIG_PATH),
        }, ensure_ascii=False, indent=2))
    else:
        with open(ACTIVE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        preview = build_preview(data)
        print(json.dumps({
            "success": True,
            "message": "preview built",
            "data": preview,
        }, ensure_ascii=False, indent=2))
