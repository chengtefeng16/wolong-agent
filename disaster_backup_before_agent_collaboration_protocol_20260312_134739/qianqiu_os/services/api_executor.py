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


class APIExecutor:
    def __init__(self):
        self.executor_name = "api_executor_v2"
        self.allowed_actions = {
            "get_request",
            "post_request",
            "put_request"
        }

    def execute(self, action_name, action_payload=None):
        if action_payload is None:
            action_payload = {}

        if action_name not in self.allowed_actions:
            return {
                "executor": self.executor_name,
                "action_name": action_name,
                "action_payload": action_payload,
                "execution_status": "simulated_failed",
                "error_code": "API_ACTION_NOT_ALLOWED",
                "error_message": f"API 动作未进入白名单：{action_name}",
                "message": f"API 执行器动作失败：{action_name}",
                "executed_at": datetime.utcnow().isoformat()
            }

        return {
            "executor": self.executor_name,
            "action_name": action_name,
            "action_payload": action_payload,
            "execution_status": "simulated_success",
            "message": f"API 执行器已接收动作：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }

    def get_request(self, endpoint, headers=None, query=None):
        if headers is None:
            headers = {}
        if query is None:
            query = {}

        return self.execute(
            action_name="get_request",
            action_payload={
                "endpoint": endpoint,
                "headers": headers,
                "query": query
            }
        )

    def post_request(self, endpoint, headers=None, body=None):
        if headers is None:
            headers = {}
        if body is None:
            body = {}

        return self.execute(
            action_name="post_request",
            action_payload={
                "endpoint": endpoint,
                "headers": headers,
                "body": body
            }
        )

    def put_request(self, endpoint, headers=None, body=None):
        if headers is None:
            headers = {}
        if body is None:
            body = {}

        return self.execute(
            action_name="put_request",
            action_payload={
                "endpoint": endpoint,
                "headers": headers,
                "body": body
            }
        )
