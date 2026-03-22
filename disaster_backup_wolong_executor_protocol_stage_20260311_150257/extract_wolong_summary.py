# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import ast
import json
import subprocess
import sys


def safe_get(data, *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def parse_output_text(text):
    text = (text or "").strip()
    if not text:
        return None

    # 优先按 JSON 解析
    try:
        return json.loads(text)
    except Exception:
        pass

    # 再按 Python 字典字面量解析
    try:
        return ast.literal_eval(text)
    except Exception:
        pass

    # 再尝试截取最外层大括号内容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
        try:
            return ast.literal_eval(candidate)
        except Exception:
            pass

    return None


def main():
    proc = subprocess.run(
        ["python", "-m", "qianqiu_os.app"],
        capture_output=True,
        text=True,
    )

    stdout_text = proc.stdout or ""
    stderr_text = proc.stderr or ""

    data = parse_output_text(stdout_text)

    if data is None:
        print("[ERROR] qianqiu_os.app 没有输出可解析内容")
        if stderr_text.strip():
            print("\n=== STDERR ===")
            print(stderr_text.strip())
        sys.exit(1)

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
        },
        "execution_task": {
            "delivery_payload": safe_get(data, "execution_task", "delivery_payload"),
            "desktop_text_payload": safe_get(
                data, "execution_task", "execution_steps", 5, "payload"
            ) if False else {
                "text": None
            },
        },
        "execution_result": {
            "execution_status": safe_get(data, "execution_result", "execution_status"),
            "api_delivery_payload": safe_get(data, "execution_result", "api_delivery_payload"),
            "browser_delivery_payload": safe_get(data, "execution_result", "browser_delivery_payload"),
            "desktop_delivery_payload": safe_get(data, "execution_result", "desktop_delivery_payload"),
        },
        "platform_governance": {
            "manual_review_required": safe_get(data, "platform_governance", "manual_review_required"),
            "governance_notes": safe_get(data, "platform_governance", "governance_notes"),
        },
    }

    # execution_task 里的 desktop_text_payload 单独从 execution_steps 中找
    execution_steps = safe_get(data, "execution_task", "execution_steps")
    if isinstance(execution_steps, list):
        desktop_text = None
        for step in execution_steps:
            if isinstance(step, dict) and step.get("executor") == "desktop" and step.get("action") == "type_text":
                payload = step.get("payload", {})
                if isinstance(payload, dict):
                    desktop_text = payload.get("text")
                break
        summary["execution_task"]["desktop_text_payload"] = {"text": desktop_text}

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if stderr_text.strip():
        print("\n=== STDERR ===")
        print(stderr_text.strip())


if __name__ == "__main__":
    main()
