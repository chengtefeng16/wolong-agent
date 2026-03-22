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
import subprocess
import ast


def safe_get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def main():
    proc = subprocess.run(
        ["python", "-m", "qianqiu_os.app"],
        capture_output=True,
        text=True
    )

    stdout = (proc.stdout or "").strip()
    if not stdout:
        print("[ERROR] qianqiu_os.app 没有输出内容")
        if proc.stderr and proc.stderr.strip():
            print("\n=== STDERR ===")
            print(proc.stderr.strip())
        return

    lines = [line for line in stdout.splitlines() if line.strip()]
    raw = lines[-1]

    try:
        data = ast.literal_eval(raw)
    except Exception:
        print("[ERROR] 无法解析 qianqiu_os.app 最后一行输出")
        print("\n=== RAW LAST LINE ===")
        print(raw)
        if proc.stderr and proc.stderr.strip():
            print("\n=== STDERR ===")
            print(proc.stderr.strip())
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
        "formatted_output": {
            "reply_status": safe_get(data, "formatted_output", "reply_status"),
            "reply_type": safe_get(data, "formatted_output", "reply_type"),
            "needs_human_handoff": safe_get(data, "formatted_output", "needs_human_handoff"),
            "customer_facing_text": safe_get(data, "formatted_output", "customer_facing_text"),
            "internal_review_text": safe_get(data, "formatted_output", "internal_review_text"),
            "channel_delivery": safe_get(data, "formatted_output", "channel_delivery"),
            "response_text": safe_get(data, "formatted_output", "response_text"),
        },
        "platform_governance": {
            "manual_review_required": safe_get(data, "platform_governance", "manual_review_required"),
            "governance_notes": safe_get(data, "platform_governance", "governance_notes"),
        },
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if proc.stderr and proc.stderr.strip():
        print("\n=== STDERR ===")
        print(proc.stderr.strip())


if __name__ == "__main__":
    main()
