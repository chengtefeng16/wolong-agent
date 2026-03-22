# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import uuid

from qianqiu_os.models.task import Task


class Scheduler:
    def __init__(self, state_manager, audit_logger, agent_registry):
        self.state_manager = state_manager
        self.audit_logger = audit_logger
        self.agent_registry = agent_registry
        self.queue = []

    def create_task(self, agent_id, task_type, input_payload):
        task = Task(
            task_id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_type=task_type,
            input_payload=input_payload
        )
        self.state_manager.create_task(task)
        self.audit_logger.info(f"Scheduler created task: {task.task_id}")
        return task

    def enqueue_task(self, task):
        self.queue.append(task)
        self.state_manager.update_task_status(task.task_id, "queued")
        self.audit_logger.info(f"Scheduler queued task: {task.task_id}")

    def dequeue_task(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def dispatch_next_task(self):
        task = self.dequeue_task()
        if not task:
            raise Exception("No task in queue.")

        try:
            self.state_manager.update_task_status(task.task_id, "planning")
            self.audit_logger.info(f"Scheduler planning task: {task.task_id}")

            agent = self.agent_registry.get(task.agent_id)
            if not agent:
                raise Exception(f"Agent not found: {task.agent_id}")

            self.state_manager.update_task_status(task.task_id, "executing")
            self.audit_logger.info(f"Scheduler dispatching task: {task.task_id}")

            result = agent.handle_task(task)
            return task, result

        except Exception as e:
            task.retry_count += 1

            if task.retry_count <= task.max_retries:
                self.state_manager.update_task_fields(task.task_id, {
                    "status": "retrying",
                    "retry_count": task.retry_count,
                    "error_message": str(e)
                })
                self.audit_logger.error(
                    f"Task retrying: {task.task_id} | retry_count={task.retry_count} | error={str(e)}"
                )
                self.queue.append(task)
                return self.dispatch_next_task()

            self.state_manager.update_task_fields(task.task_id, {
                "status": "failed",
                "retry_count": task.retry_count,
                "error_message": str(e)
            })
            self.audit_logger.error(
                f"Task failed after retries: {task.task_id} | retry_count={task.retry_count} | error={str(e)}"
            )
            raise