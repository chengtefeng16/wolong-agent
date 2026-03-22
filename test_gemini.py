# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import os
from google import genai

print("API KEY =", os.getenv("GEMINI_API_KEY"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents="hello"
    )
    print("Gemini 回复：")
    print(response.text)
except Exception as e:
    print("❌ Gemini 调用失败：")
    print(e)

