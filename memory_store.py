# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from datetime import datetime, timezone
import json
from pathlib import Path

MEM_PATH = Path(__file__).parent / "memory_chat.json"

def load_history():
    if MEM_PATH.exists():
        return json.loads(MEM_PATH.read_text(encoding="utf-8"))
    return []

def append_message(role: str, content: str):
    history = load_history()
    history.append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "role": role,
        "content": content
    })
    MEM_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def clear_history():
    if MEM_PATH.exists():
        MEM_PATH.unlink()

