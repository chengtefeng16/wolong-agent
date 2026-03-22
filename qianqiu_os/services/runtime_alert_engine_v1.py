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
ALERT_DIR = BASE_DIR / "runtime_alerts"
RUNTIME_GOVERNANCE_DIR = BASE_DIR / "runtime_governance"

ALERT_LATEST_PATH = ALERT_DIR / "runtime_alerts_latest.json"


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


class RuntimeAlertEngineV1:
    def _load_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        for path in MEMORY_DIR.glob("*.json"):
            data = _read_json(path, {})
            if isinstance(data, dict) and data:
                profiles.append(data)
        return profiles

    def _collect_delivery_alerts(self) -> List[Dict[str, Any]]:
        delivery_dir = RUNTIME_GOVERNANCE_DIR / "delivery_logs"
        alerts = []
        if not delivery_dir.exists():
            return alerts

        for path in sorted(delivery_dir.glob("*.json"))[-10:]:
            data = _read_json(path, {})
            if not isinstance(data, dict):
                continue
            result = data.get("result", {}) or {}
            error_code = result.get("error_code")
            if error_code in ["readonly_mode_blocked_send", "adapter_disabled", "whatsapp_auto_reply_disabled"]:
                alerts.append(
                    {
                        "type": "delivery_blocked",
                        "level": "high",
                        "title": "外发被治理层拦截",
                        "message": f"客户 {data.get('customer_id') or '-'} 的外发被拦截，原因：{error_code}",
                        "customer_id": data.get("customer_id"),
                        "session_id": data.get("session_id"),
                        "created_at": data.get("logged_at") or _now_str(),
                    }
                )
        return alerts

    def _collect_profile_alerts(self) -> List[Dict[str, Any]]:
        profiles = self._load_profiles()
        alerts = []

        for profile in profiles:
            latest = profile.get("latest_profile", {}) or {}
            customer_id = profile.get("customer_id")
            customer_name = profile.get("customer_name") or customer_id

            bucket = latest.get("bucket", "")
            priority = latest.get("priority", "")
            stage = latest.get("business_stage", "")
            needs_human_review = bool(latest.get("needs_human_review", False))
            summary = latest.get("business_summary", "")

            if bucket == "准车商":
                alerts.append(
                    {
                        "type": "high_intent_customer",
                        "level": "high",
                        "title": "发现高意向客户",
                        "message": f"{customer_name} 被判断为准车商，建议优先人工跟进。",
                        "customer_id": customer_id,
                        "created_at": latest.get("updated_at") or _now_str(),
                    }
                )

            if needs_human_review and priority in ["high", "medium"]:
                alerts.append(
                    {
                        "type": "manual_review_required",
                        "level": "high" if priority == "high" else "medium",
                        "title": "需要人工接管",
                        "message": f"{customer_name} 当前需要人工查看。摘要：{summary}",
                        "customer_id": customer_id,
                        "created_at": latest.get("updated_at") or _now_str(),
                    }
                )

            if stage == "已进入报价准备":
                alerts.append(
                    {
                        "type": "quote_ready",
                        "level": "medium",
                        "title": "客户已进入报价准备",
                        "message": f"{customer_name} 已进入报价准备阶段，建议尽快报价。",
                        "customer_id": customer_id,
                        "created_at": latest.get("updated_at") or _now_str(),
                    }
                )

        return alerts

    def build_alerts(self) -> Dict[str, Any]:
        alerts = []
        alerts.extend(self._collect_profile_alerts())
        alerts.extend(self._collect_delivery_alerts())

        # 去重
        unique = []
        seen = set()
        for item in alerts:
            key = (item.get("type"), item.get("customer_id"), item.get("message"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        level_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for item in unique:
            level = item.get("level", "low")
            if level not in level_counts:
                level = "low"
            level_counts[level] += 1

        payload = {
            "generated_at": _now_str(),
            "alert_name": "runtime_alerts_latest",
            "count": len(unique),
            "level_counts": level_counts,
            "items": unique,
        }

        _write_json(ALERT_LATEST_PATH, payload)

        dated_path = ALERT_DIR / f"runtime_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _write_json(dated_path, payload)

        return {
            "success": True,
            "alert_latest_path": str(ALERT_LATEST_PATH),
            "dated_alert_path": str(dated_path),
            "count": len(unique),
            "level_counts": level_counts,
        }


if __name__ == "__main__":
    print(json.dumps(RuntimeAlertEngineV1().build_alerts(), ensure_ascii=False, indent=2))
