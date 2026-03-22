# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "facebook_channel_runtime_config_v1.json"


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


class FacebookChannelReadinessCheckV1:
    def run(self) -> Dict[str, Any]:
        cfg = _read_json(CONFIG_PATH, {})
        if not isinstance(cfg, dict):
            cfg = {}

        page_id = str(cfg.get("page_id") or "").strip()
        token = str(cfg.get("page_access_token") or "").strip()
        verify_token = str(cfg.get("verify_token") or "").strip()
        webhook_path = str(cfg.get("webhook_path") or "").strip()

        missing = []
        if not page_id:
            missing.append("FACEBOOK_PAGE_ID")
        if not token:
            missing.append("FACEBOOK_PAGE_ACCESS_TOKEN")
        if not verify_token:
            missing.append("FACEBOOK_VERIFY_TOKEN")
        if not webhook_path:
            missing.append("FACEBOOK_WEBHOOK_PATH")

        runtime_mode = str(cfg.get("runtime_mode") or "readonly").strip() or "readonly"
        delivery_mode = str(cfg.get("delivery_mode") or "dry_run").strip() or "dry_run"

        return {
            "success": True,
            "channel": "facebook_messenger",
            "config_path": str(CONFIG_PATH),
            "enabled": bool(cfg.get("enabled", False)),
            "runtime_mode": runtime_mode,
            "delivery_mode": delivery_mode,
            "auto_reply": bool(cfg.get("auto_reply", False)),
            "auto_dispatch": bool(cfg.get("auto_dispatch", False)),
            "has_page_id": bool(page_id),
            "has_page_access_token": bool(token),
            "has_verify_token": bool(verify_token),
            "has_webhook_path": bool(webhook_path),
            "missing_items": missing,
            "ready_for_readonly": bool(cfg.get("enabled", False)) and len(missing) == 0 and runtime_mode == "readonly",
            "ready_for_dry_run": bool(cfg.get("enabled", False)) and len(missing) == 0 and delivery_mode == "dry_run",
            "ready_for_real_send": False
        }


if __name__ == "__main__":
    print(json.dumps(FacebookChannelReadinessCheckV1().run(), ensure_ascii=False, indent=2))
