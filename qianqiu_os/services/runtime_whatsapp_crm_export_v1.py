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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"
EXPORT_DIR = BASE_DIR / "runtime_exports" / "crm"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class RuntimeWhatsAppCrmExportV1:
    def _load_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        for path in MEMORY_DIR.glob("*.json"):
            data = _read_json(path, {})
            if isinstance(data, dict) and data:
                profiles.append(data)
        return profiles

    def _should_export(self, profile: Dict[str, Any]) -> bool:
        latest = profile.get("latest_profile", {}) or {}
        bucket = latest.get("bucket", "")
        priority = latest.get("priority", "")
        needs_human_review = bool(latest.get("needs_human_review", False))
        business_stage = latest.get("business_stage", "")

        if bucket in ["准车商", "疑似车商"]:
            return True
        if priority in ["high", "medium"] and needs_human_review:
            return True
        if business_stage in ["已进入需求确认", "已进入报价准备"]:
            return True
        return False

    def _build_export_row(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        latest = profile.get("latest_profile", {}) or {}
        return {
            "customer_id": profile.get("customer_id"),
            "customer_name": profile.get("customer_name"),
            "country": profile.get("country"),
            "bucket": latest.get("bucket"),
            "confidence": latest.get("confidence"),
            "priority": latest.get("priority"),
            "needs_human_review": latest.get("needs_human_review"),
            "models": latest.get("models", []),
            "quantity": latest.get("quantity", 0),
            "destination_country": latest.get("destination_country", ""),
            "conditions": latest.get("conditions", []),
            "price_signals": latest.get("price_signals", []),
            "business_summary": latest.get("business_summary", ""),
            "business_stage": latest.get("business_stage", ""),
            "next_action": latest.get("next_action", ""),
            "judgement_reason": latest.get("judgement_reason", ""),
            "updated_at": latest.get("updated_at", ""),
        }

    def export(self) -> Dict[str, Any]:
        profiles = self._load_profiles()
        export_rows = []

        for profile in profiles:
            if self._should_export(profile):
                export_rows.append(self._build_export_row(profile))

        export_payload = {
            "exported_at": _now_str(),
            "export_name": "runtime_whatsapp_crm_export_v1",
            "count": len(export_rows),
            "items": export_rows,
        }

        export_path = EXPORT_DIR / "crm_export_latest.json"
        _write_json(export_path, export_payload)

        dated_export_path = EXPORT_DIR / f"crm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _write_json(dated_export_path, export_payload)

        return {
            "success": True,
            "export_path": str(export_path),
            "dated_export_path": str(dated_export_path),
            "count": len(export_rows),
        }


if __name__ == "__main__":
    print(json.dumps(RuntimeWhatsAppCrmExportV1().export(), ensure_ascii=False, indent=2))
