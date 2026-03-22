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

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

BASE_DIR = CURRENT_FILE.parents[1]
TAKEOVER_DIR = BASE_DIR / "runtime_governance" / "manual_takeover_tickets"
MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"
ALERT_LATEST_PATH = BASE_DIR / "runtime_alerts" / "runtime_alerts_latest.json"

WORKBENCH_PATH = BASE_DIR / "runtime_views" / "manual_takeover_workbench.json"
WOLONG_PUBLIC_PATH = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "views" / "manual_takeover_workbench.json"
WOLONG_DIST_PATH = PROJECT_ROOT / "wolong_h5_console" / "dist" / "runtime" / "views" / "manual_takeover_workbench.json"


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


def _priority_weight(priority: str) -> int:
    mapping = {"high": 3, "medium": 2, "low": 1}
    return mapping.get((priority or "").lower(), 0)


class RuntimeManualTakeoverWorkbenchV1:
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        profiles = {}
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        for path in MEMORY_DIR.glob("*.json"):
            data = _read_json(path, {})
            if isinstance(data, dict) and data:
                customer_id = str(data.get("customer_id") or "").strip()
                if customer_id:
                    profiles[customer_id] = data
        return profiles

    def _load_alert_map(self) -> Dict[str, List[Dict[str, Any]]]:
        alert_data = _read_json(ALERT_LATEST_PATH, {})
        items = alert_data.get("items", []) if isinstance(alert_data, dict) else []
        alert_map: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            customer_id = str(item.get("customer_id") or "").strip()
            if not customer_id:
                continue
            alert_map.setdefault(customer_id, []).append(item)
        return alert_map

    def _ticket_items(self, profiles: Dict[str, Dict[str, Any]], alert_map: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        TAKEOVER_DIR.mkdir(parents=True, exist_ok=True)

        for path in TAKEOVER_DIR.glob("*.json"):
            ticket = _read_json(path, {})
            if not isinstance(ticket, dict) or not ticket:
                continue

            customer_id = str(ticket.get("customer_id") or "").strip()
            profile = profiles.get(customer_id, {})
            latest = profile.get("latest_profile", {}) if isinstance(profile, dict) else {}
            customer_name = (
                profile.get("customer_name")
                or latest.get("customer_name")
                or customer_id
                or "未知客户"
            )

            priority = latest.get("priority") or "medium"
            stage = latest.get("business_stage") or "待补充阶段"
            summary = latest.get("business_summary") or latest.get("judgement_reason") or ""
            next_action = latest.get("next_action") or "建议人工查看并继续推进。"

            items.append({
                "ticket_id": path.stem,
                "source": "manual_takeover_ticket",
                "customer_id": customer_id,
                "customer_name": customer_name,
                "country": profile.get("country") or latest.get("destination_country") or "",
                "bucket": latest.get("bucket") or "",
                "priority": priority,
                "business_stage": stage,
                "summary": summary,
                "next_action": next_action,
                "takeover_reason": ticket.get("reason") or "waiting_human_takeover",
                "takeover_status": ticket.get("status") or "waiting_human_takeover",
                "created_at": ticket.get("created_at") or _now_str(),
                "alert_count": len(alert_map.get(customer_id, [])),
            })

        return items

    def _profile_generated_items(self, profiles: Dict[str, Dict[str, Any]], existing_customer_ids: set[str], alert_map: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for customer_id, profile in profiles.items():
            if customer_id in existing_customer_ids:
                continue

            latest = profile.get("latest_profile", {}) or {}
            if not latest.get("needs_human_review", False):
                continue

            customer_name = profile.get("customer_name") or customer_id
            priority = latest.get("priority") or "medium"

            items.append({
                "ticket_id": f"virtual_takeover_{customer_id}",
                "source": "profile_needs_human_review",
                "customer_id": customer_id,
                "customer_name": customer_name,
                "country": profile.get("country") or latest.get("destination_country") or "",
                "bucket": latest.get("bucket") or "",
                "priority": priority,
                "business_stage": latest.get("business_stage") or "待补充阶段",
                "summary": latest.get("business_summary") or latest.get("judgement_reason") or "",
                "next_action": latest.get("next_action") or "建议人工接手继续推进。",
                "takeover_reason": "needs_human_review",
                "takeover_status": "waiting_human_takeover",
                "created_at": latest.get("updated_at") or _now_str(),
                "alert_count": len(alert_map.get(customer_id, [])),
            })
        return items

    def build(self) -> Dict[str, Any]:
        profiles = self._load_profiles()
        alert_map = self._load_alert_map()

        ticket_items = self._ticket_items(profiles, alert_map)
        existing_customer_ids = {str(x.get("customer_id") or "").strip() for x in ticket_items}
        virtual_items = self._profile_generated_items(profiles, existing_customer_ids, alert_map)

        items = ticket_items + virtual_items

        items.sort(
            key=lambda x: (
                -_priority_weight(x.get("priority", "")),
                -(1 if x.get("takeover_status") == "waiting_human_takeover" else 0),
                x.get("created_at", ""),
            )
        )

        level_counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for item in items:
            p = (item.get("priority") or "low").lower()
            if p not in level_counts:
                p = "low"
            level_counts[p] += 1

        payload = {
            "generated_at": _now_str(),
            "workbench_name": "manual_takeover_workbench_latest",
            "count": len(items),
            "level_counts": level_counts,
            "items": items,
        }

        _write_json(WORKBENCH_PATH, payload)
        _write_json(WOLONG_PUBLIC_PATH, payload)
        _write_json(WOLONG_DIST_PATH, payload)

        dated_path = BASE_DIR / "runtime_views" / f"manual_takeover_workbench_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _write_json(dated_path, payload)

        return {
            "success": True,
            "workbench_path": str(WORKBENCH_PATH),
            "wolong_public_path": str(WOLONG_PUBLIC_PATH),
            "wolong_dist_path": str(WOLONG_DIST_PATH),
            "dated_path": str(dated_path),
            "count": len(items),
            "level_counts": level_counts,
        }


if __name__ == "__main__":
    print(json.dumps(RuntimeManualTakeoverWorkbenchV1().build(), ensure_ascii=False, indent=2))
