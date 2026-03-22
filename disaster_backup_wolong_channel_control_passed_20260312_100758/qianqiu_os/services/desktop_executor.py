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


class DesktopExecutor:
    def __init__(self):
        self.executor_name = "desktop_executor_v2"
        self.allowed_actions = {
            "move_mouse",
            "click",
            "type_text",
            "press_key",
            "open_app"
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
                "error_code": "DESKTOP_ACTION_NOT_ALLOWED",
                "error_message": f"桌面动作未进入白名单：{action_name}",
                "message": f"桌面执行器动作失败：{action_name}",
                "executed_at": datetime.utcnow().isoformat()
            }

        return {
            "executor": self.executor_name,
            "action_name": action_name,
            "action_payload": action_payload,
            "execution_status": "simulated_success",
            "message": f"桌面执行器已接收动作：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }

    def move_mouse(self, x, y):
        return self.execute(
            action_name="move_mouse",
            action_payload={
                "x": x,
                "y": y
            }
        )

    def click(self, button="left", click_count=1):
        return self.execute(
            action_name="click",
            action_payload={
                "button": button,
                "click_count": click_count
            }
        )

    def type_text(self, text):
        return self.execute(
            action_name="type_text",
            action_payload={
                "text": text
            }
        )

    def press_key(self, key_name):
        return self.execute(
            action_name="press_key",
            action_payload={
                "key_name": key_name
            }
        )

    def open_app(self, app_name):
        return self.execute(
            action_name="open_app",
            action_payload={
                "app_name": app_name
            }
        )
