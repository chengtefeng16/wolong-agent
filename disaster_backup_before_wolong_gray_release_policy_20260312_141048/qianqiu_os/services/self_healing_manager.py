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


class SelfHealingManager:
    def __init__(self):
        self.module_name = "self_healing_manager_v5"

    def build_heartbeat(self, module_name, status="alive", details=None):
        if details is None:
            details = {}

        return {
            "module_name": module_name,
            "heartbeat_status": status,
            "details": details,
            "reported_at": datetime.utcnow().isoformat()
        }

    def build_health_snapshot(self, execution_task=None, execution_result=None):
        if execution_task is None:
            execution_task = {}
        if execution_result is None:
            execution_result = {}

        return {
            "module_name": self.module_name,
            "system_health": "healthy" if execution_result.get("failed_step_count", 0) == 0 else "warning",
            "execution_id": execution_task.get("execution_id"),
            "task_id": execution_task.get("task_id"),
            "execution_status": execution_result.get("execution_status"),
            "failed_step_count": execution_result.get("failed_step_count", 0),
            "checked_at": datetime.utcnow().isoformat()
        }

    def analyze_execution_failure(self, execution_task=None, execution_result=None):
        if execution_task is None:
            execution_task = {}
        if execution_result is None:
            execution_result = {}

        failed_steps = execution_result.get("failed_steps", [])
        if not failed_steps:
            return {
                "healing_status": "not_needed",
                "healing_level": "none",
                "healing_actions": [],
                "healing_reason": "当前没有检测到失败步骤。",
                "generated_at": datetime.utcnow().isoformat()
            }

        healing_actions = []
        healing_level = "light"

        for item in failed_steps:
            executor = item.get("executor")
            action = item.get("action")
            error_code = item.get("error_code")

            if executor == "browser":
                healing_actions.append({
                    "type": "retry_browser_action",
                    "target_executor": "browser",
                    "target_action": action,
                    "error_code": error_code,
                    "retry_attempts": 1,
                    "healing_strategy": "refresh_or_retry_browser_step",
                    "repair_action": "refresh_page",
                    "repair_payload": {
                        "reason": "browser_step_failed"
                    }
                })
            elif executor == "desktop":
                healing_actions.append({
                    "type": "retry_desktop_action",
                    "target_executor": "desktop",
                    "target_action": action,
                    "error_code": error_code,
                    "retry_attempts": 1,
                    "healing_strategy": "retry_desktop_input_step",
                    "repair_action": "retype_text",
                    "repair_payload": {
                        "reason": "desktop_step_failed"
                    }
                })
            elif executor == "api":
                healing_actions.append({
                    "type": "retry_api_action",
                    "target_executor": "api",
                    "target_action": action,
                    "error_code": error_code,
                    "retry_attempts": 1,
                    "healing_strategy": "retry_api_request_step",
                    "repair_action": "resend_request",
                    "repair_payload": {
                        "reason": "api_step_failed"
                    }
                })
            else:
                healing_actions.append({
                    "type": "retry_generic_step",
                    "target_executor": executor,
                    "target_action": action,
                    "error_code": error_code,
                    "retry_attempts": 1,
                    "healing_strategy": "generic_retry_step",
                    "repair_action": "retry_once",
                    "repair_payload": {
                        "reason": "generic_step_failed"
                    }
                })

        return {
            "healing_status": "suggested",
            "healing_level": healing_level,
            "healing_actions": healing_actions,
            "healing_reason": "检测到执行失败步骤，建议进入差异化轻度自愈流程。",
            "generated_at": datetime.utcnow().isoformat()
        }

    def execute_healing_plan(self, healing_plan=None):
        if healing_plan is None:
            healing_plan = {}

        healing_actions = healing_plan.get("healing_actions", [])
        healing_status = healing_plan.get("healing_status")

        if healing_status == "not_needed" or not healing_actions:
            return {
                "healing_execution_status": "skipped",
                "executed_action_count": 0,
                "retry_result": {
                    "retry_attempted": False,
                    "retry_success_count": 0,
                    "retry_failed_count": 0
                },
                "repair_result": {
                    "repair_attempted": False,
                    "repair_success_count": 0,
                    "repair_failed_count": 0
                },
                "healing_execution_logs": [],
                "healing_summary": "当前无需执行自愈动作。",
                "executed_at": datetime.utcnow().isoformat()
            }

        healing_execution_logs = []
        retry_success_count = 0
        retry_failed_count = 0
        repair_success_count = 0
        repair_failed_count = 0

        for item in healing_actions:
            action_type = item.get("type")
            target_executor = item.get("target_executor")
            target_action = item.get("target_action")
            error_code = item.get("error_code")
            retry_attempts = item.get("retry_attempts", 1)
            healing_strategy = item.get("healing_strategy")
            repair_action = item.get("repair_action")
            repair_payload = item.get("repair_payload", {})

            retry_outcome = "simulated_success"
            repair_outcome = "simulated_success"

            if retry_outcome == "simulated_success":
                retry_success_count += 1
            else:
                retry_failed_count += 1

            if repair_outcome == "simulated_success":
                repair_success_count += 1
            else:
                repair_failed_count += 1

            healing_execution_logs.append({
                "action_type": action_type,
                "target_executor": target_executor,
                "target_action": target_action,
                "error_code": error_code,
                "retry_attempts": retry_attempts,
                "healing_strategy": healing_strategy,
                "repair_action": repair_action,
                "repair_payload": repair_payload,
                "execution_status": "simulated_done",
                "retry_outcome": retry_outcome,
                "repair_outcome": repair_outcome,
                "message": f"已执行差异化轻度自愈动作模拟：{target_executor} -> {repair_action}",
                "logged_at": datetime.utcnow().isoformat()
            })

        return {
            "healing_execution_status": "done",
            "executed_action_count": len(healing_actions),
            "retry_result": {
                "retry_attempted": True,
                "retry_success_count": retry_success_count,
                "retry_failed_count": retry_failed_count
            },
            "repair_result": {
                "repair_attempted": True,
                "repair_success_count": repair_success_count,
                "repair_failed_count": repair_failed_count
            },
            "healing_execution_logs": healing_execution_logs,
            "healing_summary": "差异化轻度自愈动作已执行模拟。",
            "executed_at": datetime.utcnow().isoformat()
        }

    def build_healing_log(self, health_snapshot, healing_plan, healing_result=None):
        if healing_result is None:
            healing_result = {}

        return {
            "module_name": self.module_name,
            "health_snapshot": health_snapshot,
            "healing_plan": healing_plan,
            "healing_result": healing_result,
            "logged_at": datetime.utcnow().isoformat()
        }
