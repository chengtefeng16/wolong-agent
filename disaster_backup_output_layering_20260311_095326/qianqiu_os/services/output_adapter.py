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
    def format_output(self, source, result):
        platform_governance = result.get("platform_governance", {}) or {}
        experience_reference = result.get("experience_reference", {}) or {}
        user_memory_context = result.get("user_memory_context", {}) or {}
        input_context = result.get("input_context", {}) or {}

        wolong_result = result.get("wolong_result", {}) or {}
        wolong_policy_result = wolong_result.get("policy_result", {}) or {}
        wolong_customer_reply = wolong_result.get("customer_reply_result", {}) or {}

        top_level_tool_result = result.get("tool_result", {}) or {}
        if isinstance(top_level_tool_result.get("tool_result"), dict):
            top_level_tool_result = top_level_tool_result.get("tool_result", {}) or {}

        tool_result = wolong_policy_result or top_level_tool_result

        reply_status, reply_type, needs_human_handoff = self._build_reply_control(
            tool_result=tool_result,
            platform_governance=platform_governance
        )

        response_text = self._build_response_text(
            tool_result=tool_result,
            platform_governance=platform_governance,
            experience_reference=experience_reference,
            needs_human_handoff=needs_human_handoff,
            wolong_customer_reply=wolong_customer_reply,
        )

        return {
            "target_source": source,
            "reply_status": reply_status,
            "reply_type": reply_type,
            "needs_human_handoff": needs_human_handoff,
            "response_text": response_text,
            "platform_governance": platform_governance,
            "experience_reference": experience_reference,
            "user_memory_context": user_memory_context,
            "input_context": input_context
        }

    def _build_reply_control(self, tool_result, platform_governance):
        if platform_governance.get("manual_review_required"):
            return "waiting_human_review", "handoff_required", True

        status = tool_result.get("status")
        if status == "block":
            return "blocked", "restricted_response", True

        return "ready_to_send", "direct_response", False

    def _build_response_text(
        self,
        tool_result,
        platform_governance,
        experience_reference,
        needs_human_handoff,
        wolong_customer_reply=None,
    ):
        wolong_customer_reply = wolong_customer_reply or {}

        status = tool_result.get("status")
        risk_level = tool_result.get("risk_level")
        warnings = tool_result.get("warnings", []) or []
        policy_summary = tool_result.get("policy_summary")
        missing_fields = tool_result.get("missing_fields", []) or []

        text_parts = []

        customer_reply_text = wolong_customer_reply.get("reply_text")
        if customer_reply_text:
            text_parts.append(customer_reply_text)

        if policy_summary:
            if text_parts:
                text_parts.append("")
            text_parts.append(f"Preliminary policy summary: {policy_summary}")

        if missing_fields:
            text_parts.append("")
            text_parts.append("Missing information for manual review:")
            for item in missing_fields:
                text_parts.append(f"- {item}")

        if platform_governance.get("manual_review_required"):
            text_parts.append("")
            text_parts.append(
                "Current status: manual review is required before sending a final confirmed conclusion."
            )

        if not customer_reply_text and not policy_summary:
            text_parts.append(f"政策判断结果：{status}")
            text_parts.append(f"风险等级：{risk_level}")

            if warnings:
                text_parts.append("风险提示：")
                for item in warnings:
                    text_parts.append(f"- {item}")

            if experience_reference.get("matched_count", 0) > 0:
                text_parts.append(
                    f"历史经验参考：过去有 {experience_reference.get('matched_count')} 条类似经验，最近一次人工结论为 {experience_reference.get('latest_decision')}。"
                )

        if needs_human_handoff:
            text_parts.append("")
            text_parts.append(
                "System action: hand off to human review. Do not send a final commitment automatically."
            )

        return "\n".join(text_parts)
