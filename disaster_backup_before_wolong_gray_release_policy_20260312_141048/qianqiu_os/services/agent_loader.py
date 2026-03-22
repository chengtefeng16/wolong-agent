# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import json
import os

from qianqiu_os.agents.wolong_agent import WolongAgent


class AgentLoader:
    def __init__(self, config_path="qianqiu_os/config/agents.json"):
        self.config_path = config_path

    def _load_config(self):
        if not os.path.exists(self.config_path):
            return []

        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_agents(self, tool_registry, audit_logger):
        configs = self._load_config()
        loaded_agents = {}

        for item in configs:
            if item.get("enabled") is not True:
                continue

            agent_id = item.get("agent_id")
            class_name = item.get("class_name")

            agent_instance = None

            if class_name == "WolongAgent":
                agent_instance = WolongAgent(tool_registry, audit_logger)

            if agent_instance is None:
                continue

            loaded_agents[agent_id] = {
                "instance": agent_instance,
                "profile": item
            }

        return loaded_agents
