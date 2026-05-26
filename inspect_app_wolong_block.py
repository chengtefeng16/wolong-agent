# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from pathlib import Path

path = Path("qianqiu_os/app.py")
text = path.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()

keywords = [
    "wolong_manager = WolongManager",
    "detect_wolong_inquiry",
    "build_wolong_task_context",
    "run_preliminary_policy_check",
    "build_customer_reply",
    "build_manual_review_summary",
    "build_wolong_result",
    "handle_inquiry",
    "formatted_output",
]

hit_lines = []
for i, line in enumerate(lines, start=1):
    for kw in keywords:
        if kw in line:
            hit_lines.append(i)
            break

if not hit_lines:
    print("没有找到 Wolong 相关代码。")
    raise SystemExit

start = max(1, min(hit_lines) - 8)
end = min(len(lines), max(hit_lines) + 12)

print(f"=== qianqiu_os/app.py : {start}-{end} ===")
for i in range(start, end + 1):
    print(f"{i:04d}: {lines[i-1]}")
