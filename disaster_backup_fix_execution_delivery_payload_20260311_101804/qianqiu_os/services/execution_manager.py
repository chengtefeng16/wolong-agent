# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class ExecutionManager:
    def build_execution_task(self, task, plan_context=None, agent_profile=None):
        plan_context = plan_context or {}
        agent_profile = agent_profile or {}

        return {
            "execution_id": f"exec_{task.task_id}",
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "agent_name": agent_profile.get("name", task.agent_id),
            "agent_domain": agent_profile.get("domain"),
            "execution_mode": "structured_execution",
            "execution_status": "pending",
            "control_flags": {
                "can_pause": True,
                "can_resume": True,
                "can_stop": True,
                "manual_lock": False,
            },
            "execution_steps": [
                {
                    "step": 1,
                    "executor": "system",
                    "action": "collect_context",
                    "status": "pending",
                    "safety_level": "low",
                    "description": "整理并确认输入上下文。",
                },
                {
                    "step": 2,
                    "executor": "tool",
                    "action": "call_policy_check_tool",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "调用 policy_check 工具完成规则判断。",
                },
                {
                    "step": 3,
                    "executor": "system",
                    "action": "apply_governance",
                    "status": "pending",
                    "safety_level": "high",
                    "description": "执行平台治理判断。",
                },
                {
                    "step": 4,
                    "executor": "api",
                    "action": "post_request",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留 API 执行器上报人工转接或状态通知。",
                    "payload": {
                        "endpoint": "/handoff/report",
                        "headers": {"X-Agent-ID": task.agent_id},
                        "body": {
                            "task_id": task.task_id,
                            "agent_id": task.agent_id,
                            "event": "human_handoff_candidate",
                        },
                    },
                },
                {
                    "step": 5,
                    "executor": "browser",
                    "action": "open_page",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留浏览器执行器动作骨架。",
                    "payload": {"url": "https://example.com"},
                },
                {
                    "step": "5_desktop",
                    "executor": "desktop",
                    "action": "type_text",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留桌面执行器文本输入动作骨架。",
                    "payload": {"text": "placeholder"},
                },
                {
                    "step": "5_desktop_key",
                    "executor": "desktop",
                    "action": "press_key",
                    "status": "pending",
                    "safety_level": "low",
                    "description": "预留桌面执行器按键动作骨架。",
                    "payload": {"key_name": "enter"},
                },
            ],
        }

    def inject_delivery_payload(self, execution_task, formatted_output):
        formatted_output = formatted_output or {}
        channel_delivery = formatted_output.get("channel_delivery", {}) or {}

        send_text = channel_delivery.get("send_text") or formatted_output.get("customer_facing_text") or ""
        internal_visible_text = channel_delivery.get("internal_visible_text") or formatted_output.get("internal_review_text") or ""
        channel_type = channel_delivery.get("channel_type")
        external_text_only = channel_delivery.get("external_text_only")

        for step in execution_task.get("execution_steps", []):
            if step.get("step") == "5_desktop":
                step["payload"] = {
                    "text": send_text
                }
                step["delivery_payload"] = {
                    "channel_type": channel_type,
                    "external_text_only": external_text_only,
                    "send_text": send_text,
                    "internal_visible_text": internal_visible_text,
                }

        execution_task["delivery_payload"] = {
            "channel_type": channel_type,
            "external_text_only": external_text_only,
            "send_text": send_text,
            "internal_visible_text": internal_visible_text,
        }
        return execution_task

    def simulate_execution(self, execution_task):
        logs = []
        failed_steps = []

        for step in execution_task.get("execution_steps", []):
            step["status"] = "done"
            executor = step.get("executor")
            action = step.get("action")

            if executor == "system":
                msg = f"执行层完成动作模拟：{action}"
                logs.append({
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": msg,
                })

            elif executor == "tool":
                msg = f"执行层完成动作模拟：{action}"
                logs.append({
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": msg,
                })

            elif executor == "api":
                payload = step.get("payload", {})
                msg = f"API 执行器已接收动作：{action}"
                logs.append({
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": msg,
                    "executor_result": {
                        "executor": "api_executor_v2",
                        "action_name": action,
                        "action_payload": payload,
                        "execution_status": "simulated_success",
                        "message": msg,
                    },
                })

            elif executor == "browser":
                payload = step.get("payload", {})
                msg = f"浏览器执行器已接收动作：{action}"
                logs.append({
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": msg,
                    "executor_result": {
                        "executor": "browser_executor_v1",
                        "action_name": action,
                        "action_payload": payload,
                        "execution_status": "simulated_success",
                        "message": msg,
                    },
                })

            elif executor == "desktop":
                payload = step.get("payload", {})
                delivery_payload = step.get("delivery_payload")
                msg = f"桌面执行器已接收动作：{action}"
                log_item = {
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": msg,
                    "executor_result": {
                        "executor": "desktop_executor_v2",
                        "action_name": action,
                        "action_payload": payload,
                        "execution_status": "simulated_success",
                        "message": msg,
                    },
                }
                if delivery_payload:
                    log_item["delivery_payload"] = delivery_payload
                logs.append(log_item)

        execution_task["execution_status"] = "done"

        return {
            "execution_status": "done",
            "executed_step_count": len(execution_task.get("execution_steps", [])),
            "failed_step_count": len(failed_steps),
            "failed_steps": failed_steps,
            "execution_logs": logs,
            "control_flags": execution_task.get("control_flags", {}),
        }
