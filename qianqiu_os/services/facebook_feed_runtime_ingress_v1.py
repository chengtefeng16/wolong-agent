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
FACEBOOK_FEED_DIR = BASE_DIR / "runtime_sessions" / "facebook_feed"
FACEBOOK_FEED_EVENTS_PATH = FACEBOOK_FEED_DIR / "feed_events_latest.json"
FACEBOOK_FEED_VIEW_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_facebook_feed.json"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WOLONG_PUBLIC_FEED_VIEW = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "views" / "h5_dashboard_facebook_feed.json"
WOLONG_DIST_FEED_VIEW = PROJECT_ROOT / "wolong_h5_console" / "dist" / "runtime" / "views" / "h5_dashboard_facebook_feed.json"


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


class FacebookFeedRuntimeIngressV1:
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

    def _extract_feed_events(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []

        for entry in entries:
            changes = entry.get("changes", []) if isinstance(entry, dict) else []
            page_id = str(entry.get("id") or "").strip()

            for change in changes:
                if not isinstance(change, dict):
                    continue

                field = str(change.get("field") or "").strip()
                value = change.get("value", {}) or {}

                if field != "feed":
                    continue

                actor = value.get("from", {}) or {}
                actor_id = str(actor.get("id") or "").strip()
                actor_name = str(actor.get("name") or "").strip()

                item = str(value.get("item") or "").strip()
                verb = str(value.get("verb") or "").strip()
                message = str(value.get("message") or "").strip()
                post_id = str(value.get("post_id") or "").strip()
                comment_id = str(value.get("comment_id") or "").strip()
                parent_id = str(value.get("parent_id") or "").strip()
                created_time = value.get("created_time")

                summary = message or f"[feed] item={item or '-'} verb={verb or '-'}"

                events.append({
                    "page_id": page_id,
                    "actor_id": actor_id,
                    "actor_name": actor_name or actor_id or "unknown_actor",
                    "field": field,
                    "item": item,
                    "verb": verb,
                    "message": message,
                    "summary": summary,
                    "post_id": post_id,
                    "comment_id": comment_id,
                    "parent_id": parent_id,
                    "created_time": created_time,
                    "received_at": _now_str(),
                    "raw_value": value,
                })

        return events

    def _write_feed_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "generated_at": _now_str(),
            "channel": "facebook_feed",
            "count": len(events),
            "items": events,
        }
        _write_json(FACEBOOK_FEED_EVENTS_PATH, payload)

        dated_path = FACEBOOK_FEED_DIR / f"feed_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _write_json(dated_path, payload)

        return {
            "latest_path": str(FACEBOOK_FEED_EVENTS_PATH),
            "dated_path": str(dated_path),
            "payload": payload,
        }

    def _write_feed_view(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats = {
            "comment_or_post": 0,
            "other_feed_events": 0,
        }

        cards = []
        for idx, event in enumerate(events):
            is_comment_like = event.get("item") in ["comment", "post", "status"] or event.get("message")
            if is_comment_like:
                stats["comment_or_post"] += 1
            else:
                stats["other_feed_events"] += 1

            cards.append({
                "id": f"facebook_feed_{idx+1}",
                "name": event.get("actor_name") or event.get("actor_id") or "unknown_actor",
                "category": "Facebook Feed",
                "country": "未知",
                "channel": "Facebook（公开互动）",
                "time": event.get("received_at", ""),
                "message": event.get("summary", ""),
                "keywords": [x for x in [event.get("item"), event.get("verb")] if x],
                "reason": f"field={event.get('field', '')} item={event.get('item', '')} verb={event.get('verb', '')}",
                "tags": [],
                "phone": event.get("actor_id", ""),
                "timeline": [
                    f"{event.get('received_at', '')} 公开互动：{event.get('summary', '')}"
                ],
                "messages": [
                    {
                        "role": "公开互动",
                        "text": event.get("summary", ""),
                        "time": event.get("received_at", ""),
                    }
                ],
                "crm_status": "feed_observe_only",
                "needs_human_review": False,
                "destination": "",
            })

        view_payload = {
            "generated_at": _now_str(),
            "channel": "facebook_feed",
            "customer_count": len(cards),
            "stats": stats,
            "customers": cards,
        }

        _write_json(FACEBOOK_FEED_VIEW_PATH, view_payload)
        _write_json(WOLONG_PUBLIC_FEED_VIEW, view_payload)
        _write_json(WOLONG_DIST_FEED_VIEW, view_payload)

        return {
            "view_path": str(FACEBOOK_FEED_VIEW_PATH),
            "customer_count": len(cards),
        }

    def sync(self) -> Dict[str, Any]:
        entries = self._extract_entries()
        events = self._extract_feed_events(entries)
        write_info = self._write_feed_events(events)
        view_info = self._write_feed_view(events)

        return {
            "success": True,
            "entry_count": len(entries),
            "feed_event_count": len(events),
            "events_path": write_info["latest_path"],
            "view_path": view_info["view_path"],
            "customer_count": view_info["customer_count"],
        }


if __name__ == "__main__":
    print(json.dumps(FacebookFeedRuntimeIngressV1().sync(), ensure_ascii=False, indent=2))
