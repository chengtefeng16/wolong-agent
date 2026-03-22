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
from copy import deepcopy
from pathlib import Path

from qianqiu_os.services.business_context_manager import BusinessContextManager


class OutputAdapter:
    CUSTOMER_CHANNELS = {"whatsapp", "facebook", "instagram", "web_chat", "whatsapp_mock"}
    INTERNAL_CHANNELS = {"h5_console", "admin_console", "review_console", "internal_audit"}

    def __init__(self):
        self.business_context_manager = BusinessContextManager()

    def format_output(self, source, result):
        platform_governance = result.get("platform_governance", {}) or {}
        experience_reference = result.get("experience_reference", {}) or {}
        user_memory_context = result.get("user_memory_context", {}) or {}
        input_context = result.get("input_context", {}) or {}
        tool_result = result.get("tool_result", {}) or {}
        wolong_result = result.get("wolong_result", {}) or {}

        reply_status, reply_type, needs_human_handoff = self._build_reply_control(
            tool_result=tool_result,
            platform_governance=platform_governance,
            wolong_result=wolong_result,
        )

        customer_facing_text = self._build_customer_facing_text(
            tool_result=tool_result,
            wolong_result=wolong_result,
            needs_human_handoff=needs_human_handoff,
        )

        internal_review_text = self._build_internal_review_text(
            tool_result=tool_result,
            platform_governance=platform_governance,
            experience_reference=experience_reference,
            wolong_result=wolong_result,
            needs_human_handoff=needs_human_handoff,
        )

        channel_delivery = self._build_channel_delivery(
            source=source,
            customer_facing_text=customer_facing_text,
            internal_review_text=internal_review_text,
        )

        response_text = self._build_debug_response_text(
            customer_facing_text=customer_facing_text,
            internal_review_text=internal_review_text,
        )

        outbound_ready = not needs_human_handoff
        outbound_block_reason = "manual_review_required" if needs_human_handoff else None
        recommended_send_text = customer_facing_text
        human_review_gate = {
            "required": needs_human_handoff,
            "reason": outbound_block_reason,
            "status": "waiting_human_review" if needs_human_handoff else "send_allowed",
        }

        business_action_result = wolong_result.get("business_action_result", {}) or {}
        wolong_delegation_policy = wolong_result.get("delegation_policy_result", {}) or {}
        runtime_delegation_policy = self._load_runtime_delegation_policy()
        whatsapp_control = self._load_whatsapp_control()

        business_context = self.business_context_manager.build_context(
            input_context=input_context,
            tool_result=tool_result,
            wolong_result=wolong_result,
            user_memory_context=user_memory_context,
        )

        delegation_policy = self._merge_delegation_policy(
            runtime_policy=runtime_delegation_policy,
            wolong_policy=wolong_delegation_policy,
            source=source,
            business_context=business_context,
        )

        if source in {"whatsapp", "whatsapp_mock"}:
            ingress_mode = whatsapp_control.get("ingress_mode", "readonly")

            if ingress_mode == "off":
                outbound_ready = False
                outbound_block_reason = "whatsapp_ingress_off"
                human_review_gate = {
                    "required": True,
                    "reason": outbound_block_reason,
                    "status": "blocked_by_runtime_control",
                }

            elif not whatsapp_control.get("auto_reply", False):
                outbound_ready = False
                outbound_block_reason = "whatsapp_auto_reply_disabled"
                human_review_gate = {
                    "required": True,
                    "reason": outbound_block_reason,
                    "status": "waiting_human_review",
                }

        return {
            "target_source": source,
            "reply_status": reply_status,
            "reply_type": reply_type,
            "needs_human_handoff": needs_human_handoff,
            "outbound_ready": outbound_ready,
            "outbound_block_reason": outbound_block_reason,
            "recommended_send_text": recommended_send_text,
            "human_review_gate": human_review_gate,
            "business_action_result": business_action_result,
            "business_context": business_context,
            "delegation_policy": delegation_policy,
            "whatsapp_control": whatsapp_control,
            "customer_facing_text": customer_facing_text,
            "internal_review_text": internal_review_text,
            "channel_delivery": channel_delivery,
            "response_text": response_text,
            "platform_governance": platform_governance,
            "experience_reference": experience_reference,
            "user_memory_context": user_memory_context,
            "input_context": input_context,
        }

    def _runtime_active_config_path(self):
        return Path(__file__).resolve().parents[1] / "runtime_governance" / "delegation_active_config.json"

    def _load_runtime_delegation_policy(self):
        path = self._runtime_active_config_path()
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("delegation_policy", {}) or {}
        except Exception:
            return {}

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

    def _merge_delegation_policy(self, runtime_policy, wolong_policy, source, business_context):
        merged = deepcopy(runtime_policy or {})
        for key, value in (wolong_policy or {}).items():
            merged[key] = value

        business_context = business_context or {}

        if not merged.get("next_action"):
            merged["next_action"] = "customer_send"

        if not merged.get("business_stage"):
            merged["business_stage"] = business_context.get("business_stage")

        if not merged.get("risk_level"):
            merged["risk_level"] = business_context.get("risk_level")

        if not merged.get("destination_country"):
            merged["destination_country"] = business_context.get("destination_country")

        if not merged.get("customer_type"):
            merged["customer_type"] = business_context.get("customer_type")

        if not merged.get("intent_type"):
            merged["intent_type"] = business_context.get("intent_type")

        if not merged.get("emotion_state"):
            merged["emotion_state"] = business_context.get("emotion_state")

        if not merged.get("target_source"):
            merged["target_source"] = source

        return merged

    def _build_reply_control(self, tool_result, platform_governance, wolong_result):
        manual_review_required = (
            platform_governance.get("manual_review_required")
            or wolong_result.get("manual_review_result", {}).get("manual_review_required")
            or tool_result.get("manual_review_required")
        )

        if manual_review_required:
            return "waiting_human_review", "handoff_required", True

        status = tool_result.get("status")
        if status == "block":
            return "blocked", "restricted_response", True

        return "ready_to_send", "direct_response", False

    def _build_customer_facing_text(self, tool_result, wolong_result, needs_human_handoff):
        customer_reply_result = wolong_result.get("customer_reply_result", {}) or {}
        customer_reply_text = customer_reply_result.get("reply_text")

        if customer_reply_text:
            return customer_reply_text

        policy_summary = tool_result.get("policy_summary")
        if policy_summary:
            if needs_human_handoff:
                return (
                    policy_summary
                    + " Please note that this is a preliminary assessment and still requires manual confirmation."
                )
            return policy_summary

        return "Your request has been received and is under review."

    def _build_internal_review_text(
        self,
        tool_result,
        platform_governance,
        experience_reference,
        wolong_result,
        needs_human_handoff,
    ):
        manual_review_result = wolong_result.get("manual_review_result", {}) or {}
        warnings = tool_result.get("warnings", []) or []
        missing_fields = tool_result.get("missing_fields", []) or []

        lines = []

        policy_summary = tool_result.get("policy_summary")
        if policy_summary:
            lines.append(f"Preliminary policy summary: {policy_summary}")

        if missing_fields:
            lines.append("Missing information for manual review:")
            for item in missing_fields:
                lines.append(f"- {item}")

        if warnings:
            lines.append("Risk warnings:")
            for item in warnings:
                lines.append(f"- {item}")

        review_summary = manual_review_result.get("review_summary")
        if review_summary:
            lines.append(f"Manual review summary: {review_summary}")

        if platform_governance.get("manual_review_required"):
            lines.append("Current status: manual review is required before sending a final confirmed conclusion.")

        if experience_reference.get("matched_count", 0) > 0:
            lines.append(
                "Historical experience reference: past similar cases = "
                f"{experience_reference.get('matched_count')}, "
                f"latest decision = {experience_reference.get('latest_decision')}."
            )

        if needs_human_handoff:
            lines.append("System action: hand off to human review. Do not send a final commitment automatically.")

        return "\n".join(lines)

    def _build_channel_delivery(self, source, customer_facing_text, internal_review_text):
        normalized_source = str(source or "").strip().lower()

        if normalized_source in self.CUSTOMER_CHANNELS:
            return {
                "channel_type": "customer_channel",
                "send_text": customer_facing_text,
                "internal_visible_text": internal_review_text,
                "external_text_only": True,
            }

        if normalized_source in self.INTERNAL_CHANNELS:
            return {
                "channel_type": "internal_channel",
                "send_text": internal_review_text,
                "internal_visible_text": internal_review_text,
                "external_text_only": False,
            }

        return {
            "channel_type": "hybrid_or_unknown",
            "send_text": customer_facing_text,
            "internal_visible_text": internal_review_text,
            "external_text_only": True,
        }

    def _build_debug_response_text(self, customer_facing_text, internal_review_text):
        if internal_review_text:
            return customer_facing_text + "\n\n--- INTERNAL REVIEW ---\n" + internal_review_text
        return customer_facing_text
