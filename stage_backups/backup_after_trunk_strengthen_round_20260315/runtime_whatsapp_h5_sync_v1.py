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
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_SESSIONS_DIR = BASE_DIR / "runtime_sessions" / "whatsapp"
RUNTIME_VIEWS_DIR = BASE_DIR / "runtime_views"
ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"

INDEX_PATH = RUNTIME_SESSIONS_DIR / "conversation_index.json"
CONVERSATIONS_DIR = RUNTIME_SESSIONS_DIR / "conversations"

DASHBOARD_PATH = RUNTIME_VIEWS_DIR / "h5_dashboard_whatsapp.json"
CONTROL_SNAPSHOT_PATH = RUNTIME_VIEWS_DIR / "whatsapp_control_snapshot.json"


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


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_whatsapp_control() -> Dict[str, Any]:
    active = _read_json(ACTIVE_CONFIG_PATH, {})
    whatsapp_control = _safe_dict(active.get("whatsapp_control"))
    return {
        "ingress_mode": whatsapp_control.get("ingress_mode", "readonly"),
        "auto_classify": bool(whatsapp_control.get("auto_classify", True)),
        "auto_tagging": bool(whatsapp_control.get("auto_tagging", True)),
        "h5_visible": bool(whatsapp_control.get("h5_visible", True)),
        "auto_reply": bool(whatsapp_control.get("auto_reply", False)),
        "auto_dispatch": bool(whatsapp_control.get("auto_dispatch", False)),
    }


def _load_index_items() -> List[Dict[str, Any]]:
    index_data = _read_json(INDEX_PATH, {})
    if isinstance(index_data, dict):
        return _safe_list(index_data.get("items"))
    if isinstance(index_data, list):
        return index_data
    return []


def _normalize_messages(messages: Any) -> List[Dict[str, Any]]:
    output = []
    for item in _safe_list(messages):
        item = _safe_dict(item)
        role = item.get("role", "customer")
        role_label = "客户" if role == "customer" else "我方"
        output.append(
            {
                "role": role_label,
                "text": item.get("text", ""),
                "time": item.get("time") or item.get("timestamp") or "—",
            }
        )
    return output


def _build_customer_card(index_item: Dict[str, Any], seq: int) -> Dict[str, Any]:
    phone = index_item.get("phone", f"unknown_{seq}")
    conv_path = CONVERSATIONS_DIR / f"{phone}.json"
    conv = _read_json(conv_path, {})

    bucket = conv.get("bucket") or index_item.get("bucket") or "待判断"
    summary = conv.get("summary") or index_item.get("latest_message") or "暂无摘要"
    wants = _safe_list(conv.get("wants"))
    conditions = _safe_list(conv.get("conditions"))
    keywords = wants + conditions

    timeline = []
    for msg in _normalize_messages(conv.get("messages")):
        timeline.append(f"{msg.get('time', '—')} {msg.get('role', '')}：{msg.get('text', '')}")

    return {
        "id": str(phone),
        "name": conv.get("customer_name") or index_item.get("customer_name") or phone,
        "category": bucket,
        "country": conv.get("country") or index_item.get("country") or "未知",
        "channel": conv.get("channel") or index_item.get("channel") or "whatsapp",
        "time": index_item.get("last_message_time") or "—",
        "message": index_item.get("latest_message") or summary,
        "keywords": keywords,
        "reason": summary,
        "tags": wants,
        "phone": phone,
        "timeline": timeline,
        "messages": _normalize_messages(conv.get("messages")),
        "crm_status": conv.get("crm_status") or index_item.get("crm_status") or "unknown",
        "needs_human_review": bool(index_item.get("needs_human_review", False)),
        "destination": conv.get("destination") or "",
    }


def _build_stats(customers: List[Dict[str, Any]]) -> Dict[str, int]:
    stats = {
        "准车商": 0,
        "疑似车商": 0,
        "个人客户": 0,
        "沟通无效": 0,
    }
    for item in customers:
        category = item.get("category", "待判断")
        if category in stats:
            stats[category] += 1
        else:
            stats["沟通无效"] += 1
    return stats


def build_dashboard() -> Dict[str, Any]:
    items = _load_index_items()
    customers = [_build_customer_card(item, i + 1) for i, item in enumerate(items)]
    stats = _build_stats(customers)

    return {
        "dashboard_name": "h5_dashboard_whatsapp",
        "source": "runtime_sessions/whatsapp",
        "customers": customers,
        "stats": stats,
        "customer_count": len(customers),
    }


def sync():
    dashboard = build_dashboard()
    control_snapshot = _load_whatsapp_control()

    _write_json(DASHBOARD_PATH, dashboard)
    _write_json(CONTROL_SNAPSHOT_PATH, control_snapshot)

    return {
        "success": True,
        "dashboard_path": str(DASHBOARD_PATH),
        "control_snapshot_path": str(CONTROL_SNAPSHOT_PATH),
        "customer_count": dashboard.get("customer_count", 0),
    }


if __name__ == "__main__":
    print(json.dumps(sync(), ensure_ascii=False, indent=2))
