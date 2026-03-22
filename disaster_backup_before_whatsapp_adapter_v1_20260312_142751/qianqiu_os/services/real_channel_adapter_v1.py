# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from pathlib import Path
import json


class RealChannelAdapterV1:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "config" / "real_channel_adapter_config_v1.json"
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def send(self, payload):
        payload = payload or {}
        channel = payload.get("channel")
        send_text = payload.get("send_text")
        customer_id = payload.get("customer_id")
        session_id = payload.get("session_id")

        if not channel:
            return self._build_result(
                success=False,
                channel=None,
                delivery_status="failed",
                error_code="invalid_payload",
                error_message="channel is required",
                retryable=False,
                fallback_action="human_review",
            )

        if not send_text:
            return self._build_result(
                success=False,
                channel=channel,
                delivery_status="failed",
                error_code="invalid_payload",
                error_message="send_text is required",
                retryable=False,
                fallback_action="human_review",
            )

        if not customer_id and not session_id:
            return self._build_result(
                success=False,
                channel=channel,
                delivery_status="failed",
                error_code="invalid_payload",
                error_message="customer_id or session_id is required",
                retryable=False,
                fallback_action="human_review",
            )

        channel_cfg = self._find_channel_config(channel)
        if not channel_cfg:
            return self._build_result(
                success=False,
                channel=channel,
                delivery_status="blocked",
                error_code="channel_not_supported",
                error_message="channel not supported by adapter config",
                retryable=False,
                fallback_action="human_review",
            )

        if not self.config.get("enabled", False):
            return self._build_result(
                success=False,
                channel=channel,
                delivery_status="pending_manual",
                error_code="adapter_disabled",
                error_message="real channel adapter is disabled",
                retryable=False,
                fallback_action="human_review",
            )

        if not channel_cfg.get("enabled", False):
            return self._build_result(
                success=False,
                channel=channel,
                delivery_status="pending_manual",
                error_code="channel_disabled",
                error_message="target channel adapter is disabled",
                retryable=False,
                fallback_action="human_review",
            )

        return self._build_result(
            success=True,
            channel=channel,
            delivery_status="sent",
            provider_message_id="mock_provider_message_id",
            error_code=None,
            error_message=None,
            retryable=False,
            fallback_action=None,
        )

    def _find_channel_config(self, channel):
        for item in self.config.get("supported_channels", []):
            if item.get("channel") == channel:
                return item
        return None

    def _build_result(
        self,
        success,
        channel,
        delivery_status,
        provider_message_id=None,
        error_code=None,
        error_message=None,
        retryable=False,
        fallback_action=None,
    ):
        return {
            "success": success,
            "channel": channel,
            "delivery_status": delivery_status,
            "provider_message_id": provider_message_id,
            "error_code": error_code,
            "error_message": error_message,
            "retryable": retryable,
            "fallback_action": fallback_action,
        }


if __name__ == "__main__":
    adapter = RealChannelAdapterV1()
    demo_result = adapter.send(
        {
            "channel": "whatsapp",
            "customer_id": "cust_demo_001",
            "session_id": "wa_session_demo_001",
            "send_text": "Hello from Wolong real adapter skeleton."
        }
    )
    print(json.dumps(demo_result, ensure_ascii=False, indent=2))
