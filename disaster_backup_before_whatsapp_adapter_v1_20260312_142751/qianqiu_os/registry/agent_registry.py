# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# qianqiu_os/registry/agent_registry.py

from qianqiu_os.agents.wolong_agent import WOLONG_AGENT_PROFILE


class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.register("wolong_agent", WOLONG_AGENT_PROFILE)

    def register(self, agent_id, agent_instance):
        self.agents[agent_id] = agent_instance

    def get(self, agent_id):
        return self.agents.get(agent_id)