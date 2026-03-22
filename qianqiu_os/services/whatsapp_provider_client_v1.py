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
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    import requests
except Exception:
    requests = None


BASE_DIR = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"
CONFIG_PATH = BASE_DIR / "config" / "real_channel_adapter_config_v1.json"


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


class WhatsAppProviderClientV1:
    def __init__(self):
        self.runtime_config = self._load_runtime_config()
        self.channel_config = self._load_channel_config()

    def _load_runtime_config(self) -> Dict[str, Any]:
        data = _read_json(ACTIVE_CONFIG_PATH, {})
        return data if isinstance(data, dict) else {}

    def _load_channel_config(self) -> Dict[str, Any]:
        data = _read_json(CONFIG_PATH, {})
        return data if isinstance(data, dict) else {}

    def _runtime_whatsapp_control(self) -> Dict[str, Any]:
        cfg = self.runtime_config.get("whatsapp_control", {}) or {}
        return {
            "ingress_mode": cfg.get("ingress_mode", "readonly"),
            "auto_reply": bool(cfg.get("auto_reply", False)),
            "auto_dispatch": bool(cfg.get("auto_dispatch", False)),
        }

    def _env_assets(self) -> Dict[str, str]:
        return {
            "token": os.getenv("WHATSAPP_API_TOKEN", "").strip(),
            "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
            "graph_api_version": os.getenv("WHATSAPP_GRAPH_API_VERSION", "v23.0").strip() or "v23.0",
        }

    def _channel_whatsapp_cfg(self) -> Dict[str, Any]:
        for item in self.channel_config.get("supported_channels", []) or []:
            if item.get("channel") == "whatsapp":
                return item if isinstance(item, dict) else {}
        return {}

    def _provider_mode(self, runtime: Dict[str, Any]) -> str:
        ingress_mode = runtime.get("ingress_mode", "readonly")
        auto_reply = bool(runtime.get("auto_reply", False))
        auto_dispatch = bool(runtime.get("auto_dispatch", False))

        if ingress_mode == "off":
            return "off"
        if ingress_mode == "readonly":
            return "readonly"
        if auto_reply and auto_dispatch:
            return "live_send"
        return "dry_run"

    def readiness(self) -> Dict[str, Any]:
        runtime = self._runtime_whatsapp_control()
        env_assets = self._env_assets()
        channel_cfg = self._channel_whatsapp_cfg()

        missing_assets = []
        if not env_assets["token"]:
            missing_assets.append("WHATSAPP_API_TOKEN")
        if not env_assets["phone_number_id"]:
            missing_assets.append("WHATSAPP_PHONE_NUMBER_ID")

        provider_mode = self._provider_mode(runtime)

        return {
            "success": True,
            "provider_name": "whatsapp_provider_client_v1",
            "runtime_mode": provider_mode,
            "runtime_whatsapp_control": runtime,
            "channel_enabled": bool(channel_cfg.get("enabled", False)),
            "channel_found": bool(channel_cfg),
            "requests_available": requests is not None,
            "graph_api_version": env_assets["graph_api_version"],
            "has_token": bool(env_assets["token"]),
            "has_phone_number_id": bool(env_assets["phone_number_id"]),
            "missing_assets": missing_assets,
            "ready_for_real_send": bool(channel_cfg.get("enabled", False))
                                   and not missing_assets
                                   and requests is not None
                                   and provider_mode == "live_send",
            "ready_for_dry_run": bool(channel_cfg.get("enabled", False))
                                 and requests is not None
                                 and provider_mode == "dry_run",
        }

    def _build_result(
        self,
        success: bool,
        delivery_status: str,
        provider_message_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        retryable: bool = False,
        fallback_action: str | None = None,
        request_url: str | None = None,
        request_payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "channel": "whatsapp",
            "delivery_status": delivery_status,
            "provider_message_id": provider_message_id,
            "error_code": error_code,
            "error_message": error_message,
            "retryable": retryable,
            "fallback_action": fallback_action,
            "request_url": request_url,
            "request_payload": request_payload,
            "logged_at": _now_str(),
        }

    def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload or {}
        send_text = str(payload.get("send_text") or "").strip()
        customer_id = str(payload.get("customer_id") or "").strip()
        to_number = str(payload.get("to_number") or customer_id or "").strip()

        if not send_text:
            return self._build_result(
                success=False,
                delivery_status="failed",
                error_code="send_text_required",
                error_message="send_text is required",
                retryable=False,
                fallback_action="human_review",
            )

        if not to_number:
            return self._build_result(
                success=False,
                delivery_status="failed",
                error_code="to_number_required",
                error_message="to_number or customer_id is required",
                retryable=False,
                fallback_action="human_review",
            )

        readiness = self.readiness()
        runtime_mode = readiness["runtime_mode"]

        if not readiness["channel_found"]:
            return self._build_result(
                success=False,
                delivery_status="blocked",
                error_code="channel_config_missing",
                error_message="whatsapp channel config not found",
                retryable=False,
                fallback_action="human_review",
            )

        if not readiness["channel_enabled"]:
            return self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="adapter_disabled",
                error_message="real channel adapter is disabled",
                retryable=False,
                fallback_action="human_review",
            )

        if runtime_mode == "off":
            return self._build_result(
                success=False,
                delivery_status="blocked",
                error_code="whatsapp_ingress_off",
                error_message="whatsapp ingress is off",
                retryable=False,
                fallback_action="human_review",
            )

        if runtime_mode == "readonly":
            return self._build_result(
                success=False,
                delivery_status="pending_manual",
                error_code="readonly_mode_blocked_send",
                error_message="readonly mode blocks outbound sending",
                retryable=False,
                fallback_action="human_review",
            )

        env_assets = self._env_assets()
        request_url = f"https://graph.facebook.com/{env_assets['graph_api_version']}/{env_assets['phone_number_id']}/messages"
        request_payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": send_text},
        }

        if runtime_mode == "dry_run":
            return self._build_result(
                success=True,
                delivery_status="dry_run_ready",
                provider_message_id=None,
                error_code=None,
                error_message=None,
                retryable=False,
                fallback_action=None,
                request_url=request_url,
                request_payload=request_payload,
            )

        if readiness["missing_assets"]:
            return self._build_result(
                success=False,
                delivery_status="failed",
                error_code="missing_real_channel_assets",
                error_message="missing assets: " + ", ".join(readiness["missing_assets"]),
                retryable=False,
                fallback_action="human_review",
                request_url=request_url,
                request_payload=request_payload,
            )

        if requests is None:
            return self._build_result(
                success=False,
                delivery_status="failed",
                error_code="requests_unavailable",
                error_message="requests package is unavailable",
                retryable=False,
                fallback_action="human_review",
                request_url=request_url,
                request_payload=request_payload,
            )

        try:
            response = requests.post(
                request_url,
                headers={
                    "Authorization": f"Bearer {env_assets['token']}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=20,
            )

            response_json = {}
            try:
                response_json = response.json()
            except Exception:
                response_json = {"raw_text": response.text}

            if 200 <= response.status_code < 300:
                provider_message_id = None
                messages = response_json.get("messages")
                if isinstance(messages, list) and messages:
                    provider_message_id = messages[0].get("id")

                return self._build_result(
                    success=True,
                    delivery_status="sent",
                    provider_message_id=provider_message_id,
                    error_code=None,
                    error_message=None,
                    retryable=False,
                    fallback_action=None,
                    request_url=request_url,
                    request_payload=request_payload,
                )

            error_message = ""
            if isinstance(response_json, dict):
                err = response_json.get("error") or {}
                error_message = err.get("message") or str(response_json)

            return self._build_result(
                success=False,
                delivery_status="failed",
                provider_message_id=None,
                error_code="provider_send_failed",
                error_message=error_message or f"http_status_{response.status_code}",
                retryable=response.status_code >= 500,
                fallback_action="human_review",
                request_url=request_url,
                request_payload=request_payload,
            )

        except Exception as e:
            return self._build_result(
                success=False,
                delivery_status="failed",
                provider_message_id=None,
                error_code="provider_exception",
                error_message=str(e),
                retryable=True,
                fallback_action="human_review",
                request_url=request_url,
                request_payload=request_payload,
            )


if __name__ == "__main__":
    client = WhatsAppProviderClientV1()
    print(json.dumps(client.readiness(), ensure_ascii=False, indent=2))
