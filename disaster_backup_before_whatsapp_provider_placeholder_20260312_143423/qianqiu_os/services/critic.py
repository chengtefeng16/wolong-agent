# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class Critic:
    def review(self, plan_context, formatted_output, tool_result, experience_reference=None):
        critic_issues = []
        critic_warnings = []
        critic_score = "pass"

        if experience_reference is None:
            experience_reference = {}

        risk_level = tool_result.get("risk_level")
        warnings = tool_result.get("warnings", [])
        status = tool_result.get("status")
        reply_status = formatted_output.get("reply_status")
        response_text = formatted_output.get("response_text", "")
        plan_steps = plan_context.get("plan_steps", [])

        required_actions = {
            "collect_input_context",
            "run_policy_check",
            "apply_platform_governance",
            "decide_human_handoff",
            "format_output"
        }

        existing_actions = {step.get("action") for step in plan_steps}

        missing_actions = required_actions - existing_actions
        if missing_actions:
            critic_issues.append(f"多步计划缺少关键步骤：{sorted(list(missing_actions))}")

        if plan_context.get("requires_precheck") is not True:
            critic_issues.append("计划中未明确要求预检查，可能存在风险。")

        if risk_level == "high" and "高风险" not in response_text and "风险等级：high" not in response_text:
            critic_warnings.append("当前任务为高风险，但输出文本对高风险的显性表达仍可更强。")

        if reply_status != "waiting_human_review" and risk_level == "high":
            critic_issues.append("高风险任务未进入人工复核路径，存在治理漏洞。")

        if warnings and "人工" not in response_text:
            critic_warnings.append("存在警告信息，但输出中对人工介入提示不足。")

        if status == "allow" and "不建议直接自动发送最终结论" not in response_text:
            critic_warnings.append("当前结果为 allow，若缺少限制性措辞，客户可能误解为已确定可落地。")

        matched_count = experience_reference.get("matched_count", 0)
        latest_decision = experience_reference.get("latest_decision")
        if matched_count > 0 and latest_decision == "approve":
            if "历史经验参考" in response_text and "仅供参考" not in response_text:
                critic_warnings.append("历史经验已被引用，但输出中未再次强调经验不能替代当前人工判断。")

        if critic_issues:
            critic_score = "fail"
        elif critic_warnings:
            critic_score = "warning"

        return {
            "critic_score": critic_score,
            "critic_issues": critic_issues,
            "critic_warnings": critic_warnings
        }