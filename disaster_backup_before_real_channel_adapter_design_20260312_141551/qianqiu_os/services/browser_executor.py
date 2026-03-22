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


class BrowserExecutor:
    def __init__(self):
        self.executor_name = "browser_executor_v1"
        self.allowed_actions = {
            "open_page",
            "search_text",
            "fill_input",
            "click_element"
        }

    def execute(self, action_name, action_payload=None):
        if action_payload is None:
            action_payload = {}

        if action_name not in self.allowed_actions:
            return self._build_error_result(
                action_name=action_name,
                action_payload=action_payload,
                error_code="BROWSER_ACTION_NOT_ALLOWED",
                error_message=f"浏览器动作未进入白名单：{action_name}"
            )

        return {
            "executor": self.executor_name,
            "action_name": action_name,
            "action_payload": action_payload,
            "execution_status": "simulated_success",
            "message": f"浏览器执行器已接收动作：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }

    def open_page(self, url):
        if not url:
            return self._build_error_result(
                action_name="open_page",
                action_payload={"url": url},
                error_code="BROWSER_URL_MISSING",
                error_message="open_page 缺少 url 参数"
            )

        return self.execute(
            action_name="open_page",
            action_payload={
                "url": url
            }
        )

    def search_text(self, keyword):
        if not keyword:
            return self._build_error_result(
                action_name="search_text",
                action_payload={"keyword": keyword},
                error_code="BROWSER_KEYWORD_MISSING",
                error_message="search_text 缺少 keyword 参数"
            )

        return self.execute(
            action_name="search_text",
            action_payload={
                "keyword": keyword
            }
        )

    def fill_input(self, field_name, value):
        if not field_name:
            return self._build_error_result(
                action_name="fill_input",
                action_payload={
                    "field_name": field_name,
                    "value": value
                },
                error_code="BROWSER_FIELD_NAME_MISSING",
                error_message="fill_input 缺少 field_name 参数"
            )

        return self.execute(
            action_name="fill_input",
            action_payload={
                "field_name": field_name,
                "value": value
            }
        )

    def click_element(self, element_name):
        if not element_name:
            return self._build_error_result(
                action_name="click_element",
                action_payload={"element_name": element_name},
                error_code="BROWSER_ELEMENT_NAME_MISSING",
                error_message="click_element 缺少 element_name 参数"
            )

        return self.execute(
            action_name="click_element",
            action_payload={
                "element_name": element_name
            }
        )

    def _build_error_result(self, action_name, action_payload, error_code, error_message):
        return {
            "executor": self.executor_name,
            "action_name": action_name,
            "action_payload": action_payload,
            "execution_status": "simulated_failed",
            "error_code": error_code,
            "error_message": error_message,
            "message": f"浏览器执行器动作失败：{action_name}",
            "executed_at": datetime.utcnow().isoformat()
        }
