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
from pathlib import Path

REPLY_PATH = Path("knowledge/replies/replies.json")

def load_replies():
    if not REPLY_PATH.exists():
        return {}
    return json.loads(REPLY_PATH.read_text(encoding="utf-8"))

