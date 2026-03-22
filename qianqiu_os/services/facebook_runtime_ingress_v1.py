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
FACEBOOK_RAW_DIR = BASE_DIR / "runtime_sessions" / "facebook"
FACEBOOK_CONVERSATION_DIR = FACEBOOK_RAW_DIR / "conversations"
FACEBOOK_INDEX_PATH = FACEBOOK_RAW_DIR / "conversation_index.json"
FACEBOOK_RUNTIME_VIEW_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_facebook.json"

WOLONG_PUBLIC_FACEBOOK_VIEW = Path(__file__).resolve().parents[2] / "wolong_h5_console" / "public" / "runtime" / "views" / "h5_dashboard_facebook.json"
WOLONG_DIST_FACEBOOK_VIEW = Path(__file__).resolve().parents[2] / "wolong_h5_console" / "dist" / "runtime" / "views" / "h5_dashboard_facebook.json"


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


class FacebookRuntimeIngressV1:
    def _extract_entries(self) -> List[Dict[str, Any]]:
        FACEBOOK_RAW_DIR.mkdir(parents=True, exist_ok=True)
        all_entries = []

        for raw_file in sorted(FACEBOOK_RAW_DIR.glob("facebook_inbound_*.json")):
            data = _read_json(raw_file, {})
            payload = data.get("payload", {}) if isinstance(data, dict) else {}
            entries = payload.get("entry", []) if isinstance(payload, dict) else []
            if isinstance(entries, list):
                all_entries.extend(entries)

        return all_entries

    def _message_items_from_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        for entry in entries:
            messaging_list = entry.get("messaging", []) if isinstance(entry, dict) else []
            for msg in messaging_list:
                if not isinstance(msg, dict):
                    continue

                sender = msg.get("sender", {}) or {}
                recipient = msg.get("recipient", {}) or {}
                message = msg.get("message", {}) or {}
                postback = msg.get("postback", {}) or {}

                sender_id = str(sender.get("id") or "").strip()
                recipient_id = str(recipient.get("id") or "").strip()
                text = str(message.get("text") or "").strip()
                postback_title = str(postback.get("title") or "").strip()
                postback_payload = str(postback.get("payload") or "").strip()

                content_text = text
                if not content_text and postback_title:
                    content_text = f"[POSTBACK] {postback_title}"
                if not content_text and postback_payload:
                    content_text = f"[POSTBACK_PAYLOAD] {postback_payload}"
                if not content_text:
                    content_text = "[UNSUPPORTED_FACEBOOK_EVENT]"

                event_time = msg.get("timestamp")
                readable_time = _now_str()

                items.append({
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "text": content_text,
                    "timestamp": event_time,
                    "time": readable_time,
                    "raw": msg,
                })

        return items

    def _group_conversations(self, message_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        grouped: Dict[str, Dict[str, Any]] = {}

        for item in message_items:
            customer_id = item.get("sender_id") or "unknown_sender"
            conv = grouped.setdefault(customer_id, {
                "customer_id": customer_id,
                "customer_name": customer_id,
                "channel": "Facebook",
                "bucket": "待判断",
                "country": "未知",
                "summary": "",
                "messages": [],
                "updated_at": _now_str(),
            })

            conv["messages"].append({
                "role": "customer",
                "text": item.get("text", ""),
                "time": item.get("time", _now_str()),
                "timestamp": item.get("timestamp"),
            })
            conv["updated_at"] = item.get("time", _now_str())
            conv["summary"] = item.get("text", "")

        return grouped

    def _write_conversations_and_index(self, grouped: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        FACEBOOK_CONVERSATION_DIR.mkdir(parents=True, exist_ok=True)

        index_items = []
        for customer_id, conv in grouped.items():
            conversation_path = FACEBOOK_CONVERSATION_DIR / f"{customer_id}.json"
            _write_json(conversation_path, conv)

            latest_message = conv["messages"][-1]["text"] if conv.get("messages") else ""
            latest_time = conv["messages"][-1]["time"] if conv.get("messages") else ""

            index_items.append({
                "customer_id": customer_id,
                "customer_name": conv.get("customer_name", customer_id),
                "channel": "Facebook",
                "bucket": conv.get("bucket", "待判断"),
                "country": conv.get("country", "未知"),
                "latest_message": latest_message,
                "last_message_time": latest_time,
                "needs_human_review": False,
            })

        index_payload = {
            "generated_at": _now_str(),
            "channel": "facebook",
            "count": len(index_items),
            "items": index_items,
        }
        _write_json(FACEBOOK_INDEX_PATH, index_payload)
        return index_payload

    def _write_runtime_views(self, index_payload: Dict[str, Any], grouped: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        customers = []
        stats_map = {
            "准车商": 0,
            "疑似车商": 0,
            "个人客户": 0,
            "沟通无效": 0,
        }

        for item in index_payload.get("items", []):
            customer_id = item.get("customer_id")
            conv = grouped.get(customer_id, {})
            bucket = conv.get("bucket", "待判断")

            if bucket in stats_map:
                stats_map[bucket] += 1
            else:
                stats_map["沟通无效"] += 1

            customers.append({
                "id": customer_id,
                "name": conv.get("customer_name", customer_id),
                "category": bucket,
                "country": conv.get("country", "未知"),
                "channel": "Facebook",
                "time": item.get("last_message_time", ""),
                "message": item.get("latest_message", ""),
                "keywords": [],
                "reason": conv.get("summary", ""),
                "tags": [],
                "phone": customer_id,
                "timeline": [
                    f"{m.get('time', '')} 客户：{m.get('text', '')}"
                    for m in conv.get("messages", [])
                ],
                "messages": [
                    {
                        "role": "客户",
                        "text": m.get("text", ""),
                        "time": m.get("time", ""),
                    }
                    for m in conv.get("messages", [])
                ],
                "crm_status": "unknown",
                "needs_human_review": False,
                "destination": "",
            })

        payload = {
            "generated_at": _now_str(),
            "channel": "facebook",
            "customer_count": len(customers),
            "stats": stats_map,
            "customers": customers,
        }

        _write_json(FACEBOOK_RUNTIME_VIEW_PATH, payload)
        _write_json(WOLONG_PUBLIC_FACEBOOK_VIEW, payload)
        _write_json(WOLONG_DIST_FACEBOOK_VIEW, payload)
        return payload

    def sync(self) -> Dict[str, Any]:
        entries = self._extract_entries()
        message_items = self._message_items_from_entries(entries)
        grouped = self._group_conversations(message_items)
        index_payload = self._write_conversations_and_index(grouped)
        view_payload = self._write_runtime_views(index_payload, grouped)

        return {
            "success": True,
            "entry_count": len(entries),
            "message_count": len(message_items),
            "conversation_count": len(grouped),
            "index_path": str(FACEBOOK_INDEX_PATH),
            "view_path": str(FACEBOOK_RUNTIME_VIEW_PATH),
            "customer_count": view_payload.get("customer_count", 0),
        }


if __name__ == "__main__":
    print(json.dumps(FacebookRuntimeIngressV1().sync(), ensure_ascii=False, indent=2))
