# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class OutputAdapter:
    CUSTOMER_CHANNELS = {"whatsapp", "facebook", "instagram", "web_chat", "whatsapp_mock"}
    INTERNAL_CHANNELS = {"h5_console", "admin_console", "review_console", "internal_audit"}

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

        return {
            "target_source": source,
            "reply_status": reply_status,
            "reply_type": reply_type,
            "needs_human_handoff": needs_human_handoff,
            "customer_facing_text": customer_facing_text,
            "internal_review_text": internal_review_text,
            "channel_delivery": channel_delivery,
            "response_text": response_text,
            "platform_governance": platform_governance,
            "experience_reference": experience_reference,
            "user_memory_context": user_memory_context,
            "input_context": input_context,
        }

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
