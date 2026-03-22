# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import google.generativeai as genai
from pyautogen import AssistantAgent, UserProxyAgent
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def create_agents():
    user_agent = UserProxyAgent(name="User")
    assistant_agent = AssistantAgent(
        name="Assistant",
        llm_config={
            "type": "gemini",
            "model": "gemini-pro",
            "api_key": GEMINI_API_KEY,
            "max_output_tokens": 512,
        },
        language="zh"
    )
    return user_agent, assistant_agent
