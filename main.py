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
from pathlib import Path
from memory_store import load_history, append_message

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("没有检测到 GEMINI_API_KEY")

def load_constitution() -> str:
    p = Path("memory/constitution_v1_3.txt")
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""

client = genai.Client(api_key=API_KEY)

def run_chat(message: str) -> str:
    # 1) 读历史
    history = load_history()

    # 2) 追加用户消息到历史
    append_message("user", message)

    # 3) 拼最近历史
    recent = history[-20:]
    contents = []

    for m in recent:
        contents.append(f"{m['role']}：{m['content']}")

    contents.append(f"user：{message}")

    # 4) 读取宪法并前置注入
    constitution = load_constitution()

    prompt = (
        "【以下内容是你的长期宪法与不可违背的行为原则】\n"
        + constitution
        + "\n\n【以下是最近对话，请严格遵循宪法进行回答】\n"
        + "\n".join(contents)
    )

    # 5) 调用 Gemini
    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=prompt
    )

    reply = response.text.strip()

    # 6) 保存 AI 回复
    append_message("assistant", reply)

    return reply

