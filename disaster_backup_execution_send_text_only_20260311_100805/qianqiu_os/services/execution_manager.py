# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from datetime import datetime

from qianqiu_os.services.browser_executor import BrowserExecutor
from qianqiu_os.services.desktop_executor import DesktopExecutor
from qianqiu_os.services.api_executor import APIExecutor


class ExecutionManager:
    def __init__(self):
        self.browser_executor = BrowserExecutor()
        self.desktop_executor = DesktopExecutor()
        self.api_executor = APIExecutor()
        self.allowed_status_transitions = {
            "ready": {"running", "stopped"},
            "running": {"paused", "stopped", "done", "partial_failed", "failed"},
            "paused": {"running", "stopped"},
            "stopped": set(),
            "done": set(),
            "partial_failed": set(),
            "failed": set()
        }

    def build_execution_task(self, task, plan_context, agent_profile=None):
        if agent_profile is None:
            agent_profile = {}

        execution_steps = []
        plan_steps = plan_context.get("plan_steps", [])

        for step in plan_steps:
            action = step.get("action")

            if action == "collect_input_context":
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "system",
                    "action": "collect_context",
                    "status": "pending",
                    "safety_level": "low",
                    "description": "整理并确认输入上下文。"
                })

            elif action == "run_policy_check":
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "tool",
                    "action": "call_policy_check_tool",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "调用 policy_check 工具完成规则判断。"
                })

            elif action == "apply_platform_governance":
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "system",
                    "action": "apply_governance",
                    "status": "pending",
                    "safety_level": "high",
                    "description": "执行平台治理判断。"
                })

            elif action == "decide_human_handoff":
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "api",
                    "action": "post_request",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留 API 执行器上报人工转接或状态通知。",
                    "payload": {
                        "endpoint": "/handoff/report",
                        "headers": {
                            "X-Agent-ID": task.agent_id
                        },
                        "body": {
                            "task_id": task.task_id,
                            "agent_id": task.agent_id,
                            "event": "human_handoff_candidate"
                        }
                    }
                })

            elif action == "format_output":
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "browser",
                    "action": "open_page",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留浏览器执行器动作骨架。",
                    "payload": {
                        "url": "https://example.com"
                    }
                })
                execution_steps.append({
                    "step": f"{step.get('step')}_desktop",
                    "executor": "desktop",
                    "action": "type_text",
                    "status": "pending",
                    "safety_level": "medium",
                    "description": "预留桌面执行器文本输入动作骨架。",
                    "payload": {
                        "text": "formatted output placeholder"
                    }
                })
                execution_steps.append({
                    "step": f"{step.get('step')}_desktop_key",
                    "executor": "desktop",
                    "action": "press_key",
                    "status": "pending",
                    "safety_level": "low",
                    "description": "预留桌面执行器按键动作骨架。",
                    "payload": {
                        "key_name": "enter"
                    }
                })

            else:
                execution_steps.append({
                    "step": step.get("step"),
                    "executor": "unknown",
                    "action": action,
                    "status": "pending",
                    "safety_level": "unknown",
                    "description": step.get("description", "")
                })

        return {
            "execution_id": f"exec_{task.task_id}",
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "agent_name": agent_profile.get("name"),
            "agent_domain": agent_profile.get("domain"),
            "execution_mode": "structured_execution",
            "execution_status": "ready",
            "control_flags": {
                "can_pause": True,
                "can_resume": True,
                "can_stop": True,
                "manual_lock": False
            },
            "execution_steps": execution_steps,
            "created_at": datetime.utcnow().isoformat()
        }

    def simulate_execution(self, execution_task):
        execution_steps = execution_task.get("execution_steps", [])
        execution_logs = []
        failed_steps = []

        self._transition_status(execution_task, "running")

        if execution_task.get("control_flags", {}).get("manual_lock") is True:
            self._transition_status(execution_task, "stopped")
            return {
                "execution_status": execution_task.get("execution_status"),
                "executed_step_count": 0,
                "failed_step_count": 0,
                "failed_steps": [],
                "execution_logs": [
                    {
                        "step": None,
                        "action": "manual_lock",
                        "executor": "system",
                        "message": "执行任务被 manual_lock 阻止，未进入执行。",
                        "logged_at": datetime.utcnow().isoformat()
                    }
                ],
                "control_flags": execution_task.get("control_flags", {})
            }

        for step in execution_steps:
            if execution_task.get("execution_status") == "paused":
                execution_logs.append({
                    "step": step.get("step"),
                    "action": step.get("action"),
                    "executor": step.get("executor"),
                    "message": "执行任务当前处于 paused 状态，后续步骤未继续执行。",
                    "logged_at": datetime.utcnow().isoformat()
                })
                break

            if execution_task.get("execution_status") == "stopped":
                execution_logs.append({
                    "step": step.get("step"),
                    "action": step.get("action"),
                    "executor": step.get("executor"),
                    "message": "执行任务当前处于 stopped 状态，后续步骤未继续执行。",
                    "logged_at": datetime.utcnow().isoformat()
                })
                break

            executor = step.get("executor")
            action = step.get("action")
            payload = step.get("payload", {})

            if executor == "browser":
                executor_result = self._run_browser_action(action, payload)
            elif executor == "desktop":
                executor_result = self._run_desktop_action(action, payload)
            elif executor == "api":
                executor_result = self._run_api_action(action, payload)
            else:
                executor_result = None

            if executor_result is not None:
                if executor_result.get("execution_status") == "simulated_failed":
                    step["status"] = "failed"
                    failed_steps.append({
                        "step": step.get("step"),
                        "executor": executor,
                        "action": action,
                        "error_code": executor_result.get("error_code"),
                        "error_message": executor_result.get("error_message")
                    })
                    execution_logs.append({
                        "step": step.get("step"),
                        "action": action,
                        "executor": executor,
                        "message": executor_result.get("message"),
                        "executor_result": executor_result,
                        "logged_at": datetime.utcnow().isoformat()
                    })
                else:
                    step["status"] = "done"
                    execution_logs.append({
                        "step": step.get("step"),
                        "action": action,
                        "executor": executor,
                        "message": executor_result.get("message"),
                        "executor_result": executor_result,
                        "logged_at": datetime.utcnow().isoformat()
                    })
            else:
                step["status"] = "done"
                execution_logs.append({
                    "step": step.get("step"),
                    "action": action,
                    "executor": executor,
                    "message": f"执行层完成动作模拟：{action}",
                    "logged_at": datetime.utcnow().isoformat()
                })

        execution_status = "done"
        if failed_steps:
            execution_status = "partial_failed"

        if execution_task.get("execution_status") not in {"paused", "stopped"}:
            self._transition_status(execution_task, execution_status)

        return {
            "execution_status": execution_task.get("execution_status"),
            "executed_step_count": len([x for x in execution_steps if x.get("status") == "done"]),
            "failed_step_count": len(failed_steps),
            "failed_steps": failed_steps,
            "execution_logs": execution_logs,
            "control_flags": execution_task.get("control_flags", {})
        }

    def pause_execution(self, execution_task):
        if execution_task.get("control_flags", {}).get("can_pause") is not True:
            return False
        return self._transition_status(execution_task, "paused")

    def resume_execution(self, execution_task):
        if execution_task.get("control_flags", {}).get("can_resume") is not True:
            return False
        return self._transition_status(execution_task, "running")

    def stop_execution(self, execution_task):
        if execution_task.get("control_flags", {}).get("can_stop") is not True:
            return False
        return self._transition_status(execution_task, "stopped")

    def _transition_status(self, execution_task, new_status):
        current_status = execution_task.get("execution_status")
        allowed_next = self.allowed_status_transitions.get(current_status, set())

        if new_status in allowed_next:
            execution_task["execution_status"] = new_status
            return True
        return False

    def _run_browser_action(self, action_name, payload):
        if action_name == "open_page":
            return self.browser_executor.open_page(payload.get("url"))
        if action_name == "search_text":
            return self.browser_executor.search_text(payload.get("keyword"))
        if action_name == "fill_input":
            return self.browser_executor.fill_input(
                payload.get("field_name"),
                payload.get("value")
            )
        if action_name == "click_element":
            return self.browser_executor.click_element(payload.get("element_name"))

        return {
            "executor": "browser_executor_v1",
            "action_name": action_name,
            "action_payload": payload,
            "execution_status": "simulated_failed",
            "error_code": "BROWSER_ACTION_UNSUPPORTED",
            "error_message": f"暂不支持的浏览器动作：{action_name}",
            "message": f"浏览器执行器动作失败：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }

    def _run_desktop_action(self, action_name, payload):
        if action_name == "move_mouse":
            return self.desktop_executor.move_mouse(
                payload.get("x"),
                payload.get("y")
            )
        if action_name == "click":
            return self.desktop_executor.click(
                payload.get("button", "left"),
                payload.get("click_count", 1)
            )
        if action_name == "type_text":
            return self.desktop_executor.type_text(payload.get("text"))
        if action_name == "press_key":
            return self.desktop_executor.press_key(payload.get("key_name"))
        if action_name == "open_app":
            return self.desktop_executor.open_app(payload.get("app_name"))

        return {
            "executor": "desktop_executor_v2",
            "action_name": action_name,
            "action_payload": payload,
            "execution_status": "simulated_failed",
            "error_code": "DESKTOP_ACTION_UNSUPPORTED",
            "error_message": f"暂不支持的桌面动作：{action_name}",
            "message": f"桌面执行器动作失败：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }

    def _run_api_action(self, action_name, payload):
        if action_name == "get_request":
            return self.api_executor.get_request(
                payload.get("endpoint"),
                payload.get("headers"),
                payload.get("query")
            )
        if action_name == "post_request":
            return self.api_executor.post_request(
                payload.get("endpoint"),
                payload.get("headers"),
                payload.get("body")
            )
        if action_name == "put_request":
            return self.api_executor.put_request(
                payload.get("endpoint"),
                payload.get("headers"),
                payload.get("body")
            )

        return {
            "executor": "api_executor_v2",
            "action_name": action_name,
            "action_payload": payload,
            "execution_status": "simulated_failed",
            "error_code": "API_ACTION_UNSUPPORTED",
            "error_message": f"暂不支持的 API 动作：{action_name}",
            "message": f"API 执行器动作失败：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }
