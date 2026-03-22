# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from qianqiu_os.services.memory_manager import MemoryManager
from qianqiu_os.services.state_manager import StateManager


class MetricsManager:
    def __init__(self):
        self.state_manager = StateManager()
        self.memory_manager = MemoryManager()

    def build_metrics_summary(self):
        tasks = self.state_manager._load()
        experience_memory = self.memory_manager.load_experience_memory()
        user_memory = self.memory_manager.load_user_memory()

        total_tasks = len(tasks)
        waiting_human_review_tasks = 0
        done_tasks = 0
        failed_tasks = 0
        queued_tasks = 0
        executing_tasks = 0
        planning_tasks = 0
        retrying_tasks = 0

        retried_task_count = 0
        failed_after_retry_tasks = 0
        max_retry_count_seen = 0
        latest_failed_task_error = None

        for task in tasks:
            status = task.get("status")
            retry_count = task.get("retry_count", 0)

            if status == "waiting_human_review":
                waiting_human_review_tasks += 1
            elif status == "done":
                done_tasks += 1
            elif status == "failed":
                failed_tasks += 1
                latest_failed_task_error = task.get("error_message")
            elif status == "queued":
                queued_tasks += 1
            elif status == "executing":
                executing_tasks += 1
            elif status == "planning":
                planning_tasks += 1
            elif status == "retrying":
                retrying_tasks += 1

            if retry_count > 0:
                retried_task_count += 1

            if status == "failed" and retry_count > 0:
                failed_after_retry_tasks += 1

            if retry_count > max_retry_count_seen:
                max_retry_count_seen = retry_count

        return {
            "total_tasks": total_tasks,
            "waiting_human_review_tasks": waiting_human_review_tasks,
            "done_tasks": done_tasks,
            "failed_tasks": failed_tasks,
            "queued_tasks": queued_tasks,
            "executing_tasks": executing_tasks,
            "planning_tasks": planning_tasks,
            "retrying_tasks": retrying_tasks,
            "retried_task_count": retried_task_count,
            "failed_after_retry_tasks": failed_after_retry_tasks,
            "max_retry_count_seen": max_retry_count_seen,
            "latest_failed_task_error": latest_failed_task_error,
            "experience_memory_count": len(experience_memory),
            "user_memory_count": len(user_memory)
        }