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
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.runtime_whatsapp_h5_sync_v1 import sync as sync_h5_views


BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_SESSIONS_DIR = BASE_DIR / "runtime_sessions" / "whatsapp"
CONVERSATIONS_DIR = RUNTIME_SESSIONS_DIR / "conversations"
INDEX_PATH = RUNTIME_SESSIONS_DIR / "conversation_index.json"


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


def _ensure_index() -> Dict[str, Any]:
    data = _read_json(
        INDEX_PATH,
        {
            "index_name": "whatsapp_conversation_index",
            "version": "2026-03-15",
            "source": "runtime_sessions/whatsapp",
            "items": [],
        },
    )
    if not isinstance(data, dict):
        data = {
            "index_name": "whatsapp_conversation_index",
            "version": "2026-03-15",
            "source": "runtime_sessions/whatsapp",
            "items": [],
        }
    if not isinstance(data.get("items"), list):
        data["items"] = []
    return data


def _upsert_index_item(index_data: Dict[str, Any], item: Dict[str, Any]):
    items: List[Dict[str, Any]] = index_data["items"]
    phone = item["phone"]
    for row in items:
        if row.get("phone") == phone:
            row.update(item)
            return
    items.append(item)


class RuntimeWhatsAppIngressV1:
    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload or {}

        phone = str(payload.get("phone") or "").strip()
        text = str(payload.get("text") or "").strip()

        if not phone:
            return {
                "success": False,
                "error_code": "phone_required",
                "error_message": "phone is required",
            }

        if not text:
            return {
                "success": False,
                "error_code": "text_required",
                "error_message": "text is required",
            }

        customer_name = payload.get("customer_name") or phone
        country = payload.get("country") or "未知"
        bucket = payload.get("bucket") or "待判断"
        crm_status = payload.get("crm_status") or "pending_export"
        needs_human_review = bool(payload.get("needs_human_review", False))
        destination = payload.get("destination") or ""
        summary = payload.get("summary") or text
        wants = payload.get("wants") or []
        conditions = payload.get("conditions") or []

        conv_path = CONVERSATIONS_DIR / f"{phone}.json"
        conv = _read_json(conv_path, {})

        if not isinstance(conv, dict) or not conv:
            conv = {
                "phone": phone,
                "customer_name": customer_name,
                "country": country,
                "channel": "whatsapp",
                "bucket": bucket,
                "destination": destination,
                "crm_status": crm_status,
                "summary": summary,
                "wants": wants,
                "conditions": conditions,
                "messages": [],
            }

        if not isinstance(conv.get("messages"), list):
            conv["messages"] = []

        conv["phone"] = phone
        conv["customer_name"] = customer_name
        conv["country"] = country
        conv["channel"] = "whatsapp"
        conv["bucket"] = bucket
        conv["destination"] = destination
        conv["crm_status"] = crm_status
        conv["summary"] = summary
        conv["wants"] = wants
        conv["conditions"] = conditions

        conv["messages"].append(
            {
                "role": "customer",
                "text": text,
                "time": payload.get("time") or _now_str(),
            }
        )

        _write_json(conv_path, conv)

        index_data = _ensure_index()
        _upsert_index_item(
            index_data,
            {
                "phone": phone,
                "customer_name": customer_name,
                "country": country,
                "channel": "whatsapp",
                "bucket": bucket,
                "latest_message": text,
                "last_message_time": payload.get("time") or _now_str(),
                "needs_human_review": needs_human_review,
                "crm_status": crm_status,
            },
        )
        _write_json(INDEX_PATH, index_data)

        sync_result = sync_h5_views()

        return {
            "success": True,
            "phone": phone,
            "conversation_path": str(conv_path),
            "index_path": str(INDEX_PATH),
            "sync_result": sync_result,
        }


if __name__ == "__main__":
    demo = RuntimeWhatsAppIngressV1().ingest(
        {
            "phone": "+70000000000",
            "customer_name": "Demo Customer",
            "country": "哈萨克斯坦",
            "bucket": "疑似车商",
            "text": "Need Prado and Camry, maybe 5 units.",
            "summary": "客户有批量采购意图，需要人工继续判断。",
            "needs_human_review": True,
        }
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2))
