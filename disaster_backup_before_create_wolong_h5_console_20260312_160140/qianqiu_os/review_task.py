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
from datetime import datetime

from qianqiu_os.services.state_manager import StateManager
from qianqiu_os.services.audit_logger import AuditLogger


EXPERIENCE_LOG_PATH = "qianqiu_os/data/experience_log.json"


def append_experience(experience_item):
    os.makedirs(os.path.dirname(EXPERIENCE_LOG_PATH), exist_ok=True)

    if not os.path.exists(EXPERIENCE_LOG_PATH):
        with open(EXPERIENCE_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    with open(EXPERIENCE_LOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(experience_item)

    with open(EXPERIENCE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    state_manager = StateManager()
    audit_logger = AuditLogger()

    task_id = input("请输入需要复核的 task_id: ").strip()
    decision = input("请输入复核结果（approve / reject）: ").strip().lower()
    note = input("请输入人工复核备注: ").strip()

    task = state_manager.get_task(task_id)
    if not task:
        print("未找到该 task_id。")
        return

    if task.get("status") != "waiting_human_review":
        print(f"该任务当前状态不是 waiting_human_review，而是：{task.get('status')}")
        return

    if decision == "approve":
        new_status = "done"
    elif decision == "reject":
        new_status = "failed"
    else:
        print("复核结果只能输入 approve 或 reject。")
        return

    state_manager.update_task_fields(task_id, {
        "status": new_status,
        "human_review_decision": decision,
        "human_review_note": note
    })

    result = task.get("result", {})
    tool_result = result.get("tool_result", {})
    input_payload = task.get("input_payload", {})
    policy_health = tool_result.get("policy_health", {})
    policy_meta = tool_result.get("policy_meta", {})

    experience_item = {
        "task_id": task_id,
        "task_type": task.get("task_type"),
        "agent_id": task.get("agent_id"),
        "country_code_or_name": input_payload.get("country_code_or_name"),
        "vehicle": input_payload.get("vehicle", {}),
        "policy_status": tool_result.get("status"),
        "risk_level": tool_result.get("risk_level"),
        "is_outdated": policy_health.get("is_outdated"),
        "confidence_level": policy_meta.get("confidence_level"),
        "human_review_decision": decision,
        "human_review_note": note,
        "created_at": datetime.utcnow().isoformat()
    }

    append_experience(experience_item)

    audit_logger.info(f"Human review completed: {task_id} | decision={decision} | note={note}")

    print("人工复核已写回成功。")
    print(f"task_id: {task_id}")
    print(f"new_status: {new_status}")
    print(f"human_review_decision: {decision}")
    print(f"human_review_note: {note}")
    print("经验已沉淀到 experience_log.json")


if __name__ == "__main__":
    main()