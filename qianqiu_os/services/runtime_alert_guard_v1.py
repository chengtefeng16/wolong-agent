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
RUNTIME_VIEW_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_whatsapp.json"
CONVERSATION_INDEX_PATH = BASE_DIR / "runtime_sessions" / "whatsapp" / "conversation_index.json"


class RuntimeAlertGuardV1:
    def _read_json(self, path: Path):
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def evaluate(self):
        alerts = []

        active_config = self._read_json(ACTIVE_CONFIG_PATH)
        runtime_view = self._read_json(RUNTIME_VIEW_PATH)
        conversation_index = self._read_json(CONVERSATION_INDEX_PATH)

        if active_config is None:
            alerts.append({
                "level": "high",
                "code": "active_config_missing",
                "message": "delegation_active_config.json is missing",
                "recommended_action": "restore_or_rebuild_active_config"
            })
            return self._build_result(alerts)

        whatsapp_control = active_config.get("whatsapp_control", {}) or {}

        if not whatsapp_control:
            alerts.append({
                "level": "high",
                "code": "whatsapp_control_missing",
                "message": "whatsapp_control is missing in active config",
                "recommended_action": "inject_default_whatsapp_control"
            })

        if whatsapp_control.get("auto_reply") is True:
            alerts.append({
                "level": "high",
                "code": "auto_reply_enabled",
                "message": "auto_reply is enabled; this may be unsafe before full real-channel validation",
                "recommended_action": "force_auto_reply_false"
            })

        if runtime_view is None:
            alerts.append({
                "level": "medium",
                "code": "runtime_view_missing",
                "message": "h5_dashboard_whatsapp.json is missing",
                "recommended_action": "rebuild_runtime_view"
            })

        if conversation_index is None:
            alerts.append({
                "level": "medium",
                "code": "conversation_index_missing",
                "message": "conversation_index.json is missing",
                "recommended_action": "rebuild_conversation_index"
            })

        if runtime_view is not None and conversation_index is not None:
            runtime_count = runtime_view.get("total_conversations")
            index_items = conversation_index.get("items", [])
            index_count = len(index_items) if isinstance(index_items, list) else None

            if runtime_count is not None and index_count is not None and runtime_count != index_count:
                alerts.append({
                    "level": "medium",
                    "code": "runtime_view_index_mismatch",
                    "message": f"runtime view count ({runtime_count}) != conversation index count ({index_count})",
                    "recommended_action": "refresh_runtime_view_from_sessions"
                })

        return self._build_result(alerts)

    def _build_result(self, alerts):
        high_count = len([a for a in alerts if a["level"] == "high"])
        medium_count = len([a for a in alerts if a["level"] == "medium"])
        low_count = len([a for a in alerts if a["level"] == "low"])

        if high_count > 0:
            overall_status = "high_risk"
        elif medium_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "alert_count": len(alerts),
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "alerts": alerts,
        }


if __name__ == "__main__":
    guard = RuntimeAlertGuardV1()
    print(json.dumps(guard.evaluate(), ensure_ascii=False, indent=2))
