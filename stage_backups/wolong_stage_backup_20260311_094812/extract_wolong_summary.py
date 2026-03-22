# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import subprocess
import ast
import json
import sys

def safe_get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur

def main():
    proc = subprocess.run(
        [sys.executable, "-m", "qianqiu_os.app"],
        capture_output=True,
        text=True,
    )

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if not stdout:
        print("[ERROR] qianqiu_os.app 没有输出内容")
        if stderr:
            print("\n=== STDERR ===")
            print(stderr)
        return

    last_line = stdout.splitlines()[-1].strip()
    try:
        data = ast.literal_eval(last_line)
    except Exception:
        print("[ERROR] 无法把最后一行解析成 Python dict")
        print("\n=== LAST LINE ===")
        print(last_line)
        if stderr:
            print("\n=== STDERR ===")
            print(stderr)
        return

    summary = {
        "wolong_result": {
            "wolong_linked": safe_get(data, "wolong_result", "wolong_linked"),
            "inquiry_detected": safe_get(data, "wolong_result", "inquiry_detected"),
            "inquiry_type": safe_get(data, "wolong_result", "inquiry_type"),
            "policy_check_executed": safe_get(data, "wolong_result", "policy_check_executed"),
            "execution_status": safe_get(data, "wolong_result", "execution_status"),
            "destination_country": safe_get(data, "wolong_result", "destination_country"),
        },
        "customer_reply_result": {
            "reply_ready": safe_get(data, "wolong_result", "customer_reply_result", "reply_ready"),
            "reply_language": safe_get(data, "wolong_result", "customer_reply_result", "reply_language"),
            "reply_status": safe_get(data, "wolong_result", "customer_reply_result", "reply_status"),
            "reply_text": safe_get(data, "wolong_result", "customer_reply_result", "reply_text"),
        },
        "manual_review_result": {
            "manual_review_required": safe_get(data, "wolong_result", "manual_review_result", "manual_review_required"),
            "review_reason": safe_get(data, "wolong_result", "manual_review_result", "review_reason"),
            "review_summary": safe_get(data, "wolong_result", "manual_review_result", "review_summary"),
        },
        "platform_governance": {
            "manual_review_required": safe_get(data, "platform_governance", "manual_review_required"),
            "governance_notes": safe_get(data, "platform_governance", "governance_notes"),
        },
        "formatted_output": {
            "reply_status": safe_get(data, "formatted_output", "reply_status"),
            "reply_type": safe_get(data, "formatted_output", "reply_type"),
            "needs_human_handoff": safe_get(data, "formatted_output", "needs_human_handoff"),
            "response_text": safe_get(data, "formatted_output", "response_text"),
        },
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if stderr:
        print("\n=== STDERR ===")
        print(stderr)

if __name__ == "__main__":
    main()
