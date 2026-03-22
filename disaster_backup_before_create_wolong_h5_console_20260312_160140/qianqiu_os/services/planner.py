# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class Planner:
    def build_plan(self, task):
        task_type = task.task_type
        agent_id = task.agent_id
        input_payload = task.input_payload

        plan_steps = []
        planner_notes = []

        plan = {
            "task_type": task_type,
            "agent_id": agent_id,
            "execution_mode": "single_step",
            "recommended_tool": None,
            "requires_precheck": False,
            "plan_steps": plan_steps,
            "planner_notes": planner_notes
        }

        if task_type == "policy_check":
            plan["recommended_tool"] = "policy_check"
            plan["requires_precheck"] = True
            plan["execution_mode"] = "multi_step"

            plan_steps.append({
                "step": 1,
                "action": "collect_input_context",
                "description": "整理输入、用户画像、渠道信息。"
            })
            plan_steps.append({
                "step": 2,
                "action": "run_policy_check",
                "description": "调用 policy_check 工具执行政策规则判断。"
            })
            plan_steps.append({
                "step": 3,
                "action": "apply_platform_governance",
                "description": "根据风险、数据新鲜度、置信度执行平台治理判断。"
            })
            plan_steps.append({
                "step": 4,
                "action": "decide_human_handoff",
                "description": "判断是否进入人工复核或人工转接。"
            })
            plan_steps.append({
                "step": 5,
                "action": "format_output",
                "description": "生成统一输出结构并准备外部回复内容。"
            })

            planner_notes.append("当前任务属于政策合规判断。")
            planner_notes.append("此任务已从单步判断升级为最小多步计划。")
            planner_notes.append("建议先执行政策规则校验，再决定是否进入人工复核。")

        if input_payload.get("source") in ["facebook", "instagram"]:
            planner_notes.append("当前任务来自外部渠道，输出时需注意是否需要人工转接。")

        user_profile = input_payload.get("user_profile", {})
        if user_profile:
            planner_notes.append("当前任务携带用户画像，可结合用户偏好做后续扩展。")

        return plan