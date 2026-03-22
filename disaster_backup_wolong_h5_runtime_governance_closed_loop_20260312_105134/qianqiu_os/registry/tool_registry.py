# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# qianqiu_os/registry/tool_registry.py

from qianqiu_os.tools.wolong_policy_tool import wolong_policy_check_tool


class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.register("wolong_policy_check_tool", wolong_policy_check_tool)

    def register(self, tool_name, tool_func):
        self.tools[tool_name] = tool_func

    def get(self, tool_name):
        return self.tools.get(tool_name)