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
from typing import Any, Dict

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.whatsapp_provider_client_v1 import WhatsAppProviderClientV1


class WhatsAppChannelAdapterV1:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "config" / "real_channel_adapter_config_v1.json"
        self.config_path = Path(config_path)
        self.base_dir = Path(__file__).resolve().parents[1]
        self.config = self._load_config()
        self.provider_client = WhatsAppProviderClientV1()

    def _now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _load_config(self):
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _runtime_active_config_path(self):
        return self.base_dir / "runtime_governance" / "delegation_active_config.json"

    def _delivery_logs_dir(self):
        return self.base_dir / "runtime_governance" / "delivery_logs"

    def _takeover_tickets_dir(self):
        return self.base_dir / "runtime_governance" / "manual_takeover_tickets"

    def _load_whatsapp_control(self):
        path = self._runtime_active_config_path()
        default_cfg = {
            "ingress_mode": "readonly",
            "auto_classify": True,
            "auto_tagging": True,
            "h5_visible": True,
            "auto_reply": False,
            "auto_dispatch": False,
        }
        if not path.exists():
            return default_cfg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = data.get("whatsapp_control", {}) or {}
            default_cfg.update(cfg)
            return default_cfg
        except Exception:
            return default_cfg

    def _find_whatsapp_config(self):
        for item in self.config.get("supported_channels", []):
            if item.get("channel") == "whatsapp":
                return item
        return None

    def _write_json(self, path: Path, data: Dict[str, Any]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _append_delivery_log(self, payload: Dict[str, Any], result: Dict[str, Any]):
        file_name = f"delivery_result_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        path = self._delivery_logs_dir() / file_name
        self._write_json(
            path,
            {
                "logged_at": self._now_str(),
                "customer_id": payload.get("customer_id"),
                "session_id": payload.get("session_id"),
                "send_text": payload.get("send_text"),
                "result": result,
            },
        )

    def _create_takeover_ticket(self, payload: Dict[str, Any], reason: str):
        file_name = f"takeover_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        path = self._takeover_tickets_dir() / file_name
        self._write_json(
            path,
            {
                "created_at": self._now_str(),
                "channel": "whatsapp",
                "customer_id": payload.get("customer_id"),
                "session_id": payload.get("session_id"),
                "reason": reason,
                "send_text": payload.get("send_text"),
                "status": "waiting_human_takeover",
            },
        )

    def _build_result(
        self,
        success,
        delivery_status,
        provider_message_id=None,
        error_code=None,
        error_message=None,
        retryable=False,
        fallback_action=None,
    ):
        return {
            "success": success,
            "channel": "whatsapp",
            "delivery_status": delivery_status,
            "provider_message_id": provider_message_id,
            "error_code": error_code,
            "error_message": error_message,
            "retryable": retryable,
            "fallback_action": fallback_action,
        }

    def send(self, payload):
        payload = payload or {}
        send_text = payload.get("send_text")
        customer_id = payload.get("customer_id")
        session_id = payload.get("session_id")

        if not send_text:
            result = self._build_result(
                success=False,
                delivery_status="failed",
                error_code="invalid_payload",
                error_message="send_text is required",
                retryable=False,
                fallback_action="human_review",
            )
            self._append_delivery_log(payload, result)
            return result

        if not customer_id and not session_id:
            result = self._build_result(
                success=False,
                delivery_status="failed",
                error_code="invalid_payload",
                error_message="customer_id or session_id is required",
                retryable=False,
                fallback_action="human_review",
            )
            self._append_delivery_log(payload, result)
            return result

        if not self.config.get("enabled", False):
            result = self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="adapter_disabled",
                error_message="real channel adapter is disabled",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "adapter_disabled")
            self._append_delivery_log(payload, result)
            return result

        channel_cfg = self._find_whatsapp_config()
        if not channel_cfg:
            result = self._build_result(
                success=False,
                delivery_status="blocked",
                error_code="channel_not_supported",
                error_message="whatsapp channel config not found",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "channel_not_supported")
            self._append_delivery_log(payload, result)
            return result

        if not channel_cfg.get("enabled", False):
            result = self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="channel_disabled",
                error_message="whatsapp adapter is disabled",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "channel_disabled")
            self._append_delivery_log(payload, result)
            return result

        whatsapp_control = self._load_whatsapp_control()

        if whatsapp_control.get("ingress_mode", "readonly") == "off":
            result = self._build_result(
                success=False,
                delivery_status="blocked",
                error_code="whatsapp_ingress_off",
                error_message="whatsapp ingress is turned off by runtime control",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "whatsapp_ingress_off")
            self._append_delivery_log(payload, result)
            return result

        if whatsapp_control.get("ingress_mode", "readonly") == "readonly":
            result = self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="readonly_mode_blocked_send",
                error_message="readonly mode blocks outbound sending",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "readonly_mode_blocked_send")
            self._append_delivery_log(payload, result)
            return result

        if not whatsapp_control.get("auto_reply", False):
            result = self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="whatsapp_auto_reply_disabled",
                error_message="whatsapp auto reply is disabled by runtime control",
                retryable=False,
                fallback_action="human_review",
            )
            self._create_takeover_ticket(payload, "whatsapp_auto_reply_disabled")
            self._append_delivery_log(payload, result)
            return result

        provider_result = self.provider_client.send_message(payload)

        result = self._build_result(
            success=provider_result.get("success", False),
            delivery_status=provider_result.get("delivery_status"),
            provider_message_id=provider_result.get("provider_message_id"),
            error_code=provider_result.get("error_code"),
            error_message=provider_result.get("error_message"),
            retryable=provider_result.get("retryable", False),
            fallback_action=provider_result.get("fallback_action"),
        )

        if not result.get("success", False):
            self._create_takeover_ticket(payload, result.get("error_code") or "provider_send_failed")

        self._append_delivery_log(payload, result)
        return result


if __name__ == "__main__":
    adapter = WhatsAppChannelAdapterV1()
    result = adapter.send(
        {
            "customer_id": "cust_demo_001",
            "session_id": "wa_session_demo_001",
            "send_text": "Hello from WhatsApp adapter.",
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
