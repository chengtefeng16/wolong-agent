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
import shutil
import subprocess
import ast
import sys

root = Path(".")
app_path = Path("qianqiu_os/app.py")

if not app_path.exists():
    raise SystemExit("[ERROR] 找不到 qianqiu_os/app.py")

candidates = [
    Path("qianqiu_os/app.py.bak_before_round5"),
    Path("qianqiu_os/app.py.bak_before_round3"),
    Path("qianqiu_os/app.py.bak_fix_wolong_import_and_block"),
    Path("qianqiu_os/app.py.bak_fix_round2"),
    Path("qianqiu_os/app.py"),
]

print("=== 开始扫描可用 app.py 候选文件 ===")
usable = []

for p in candidates:
    if not p.exists():
        continue
    try:
        text = p.read_text(encoding="utf-8")
        ast.parse(text)
        usable.append((p, text))
        print(f"[OK] 可解析: {p}")
    except Exception as e:
        print(f"[SKIP] 不可解析: {p} -> {e}")

if not usable:
    raise SystemExit("[ERROR] 所有候选 app.py 都已经坏掉，当前无法自动恢复。")

# 优先使用最前面的、可解析的备份
source_path, text = usable[0]
print(f"\n[OK] 选中恢复源: {source_path}")

# 先做一份当前文件的灾难备份
backup_now = Path("qianqiu_os/app.py.bak_before_recover_full")
shutil.copy2(app_path, backup_now)
print(f"[OK] 当前 app.py 已备份到: {backup_now}")

# -------------------------------------------------
# 1) 修正导入
# -------------------------------------------------
text = text.replace(
    "from qianqiu_os.agents.agent_loader import AgentLoader",
    "from qianqiu_os.services.agent_loader import AgentLoader",
)

# -------------------------------------------------
# 2) 整体替换 Wolong 大块
# -------------------------------------------------
start_marker = '        task, result = scheduler.dispatch_next_task()'
end_marker = '        result["platform_governance"] = platform_governance'

start = text.find(start_marker)
end = text.find(end_marker)

if start == -1 or end == -1 or end <= start:
    print("[ERROR] 在恢复源里没找到 Wolong 大块起止标记。")
    print("start =", start)
    print("end   =", end)
    sys.exit(1)

end = end + len(end_marker)

new_block = """        task, result = scheduler.dispatch_next_task()

        plan_context = planner.build_plan(task)

        experience_reference = find_similar_experience(
            task.input_payload,
            result.get("tool_result", {}),
        )
        result["experience_reference"] = experience_reference

        memory_context = memory_manager.get_memory_summary()
        result["memory_context"] = memory_context

        result["user_memory_context"] = user_memory_context
        result["input_context"] = incoming_input
        result["plan_context"] = plan_context
        result["agent_profile"] = agent_profiles.get(task.agent_id)

        wolong_result = wolong_manager.handle_inquiry(
            incoming_input=incoming_input,
            user_memory_context=user_memory_context,
        )
        result["wolong_result"] = wolong_result

        platform_governance = build_platform_governance(result)

        wolong_manual_review_required = (
            result.get("wolong_result", {})
            .get("manual_review_result", {})
            .get("manual_review_required", False)
        )

        if wolong_manual_review_required:
            platform_governance["manual_review_required"] = True
            platform_governance.setdefault("governance_notes", [])
            platform_governance["governance_notes"].append(
                "Wolong preliminary review requires human confirmation."
            )

        result["platform_governance"] = platform_governance"""

text = text[:start] + new_block + text[end:]

# 再做一次语法检查，确认写回前文本本身没坏
try:
    ast.parse(text)
    print("[OK] 替换后的 app.py 文本语法通过")
except Exception as e:
    print("[ERROR] 替换后的 app.py 文本仍然语法错误：")
    print(e)
    sys.exit(1)

# -------------------------------------------------
# 3) 写回 app.py
# -------------------------------------------------
app_path.write_text(text, encoding="utf-8")
print(f"[OK] 已写回: {app_path}")

# -------------------------------------------------
# 4) 生成一个更稳的摘要脚本
# -------------------------------------------------
extract_path = Path("extract_wolong_summary.py")
extract_code = r'''import subprocess
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
'''
extract_path.write_text(extract_code, encoding="utf-8")
print(f"[OK] 已重写: {extract_path}")

# -------------------------------------------------
# 5) 自动验证
# -------------------------------------------------
commands = [
    ["python", "-m", "py_compile", "qianqiu_os/managers/wolong_manager.py"],
    ["python", "-m", "py_compile", "qianqiu_os/app.py", "qianqiu_os/services/output_adapter.py"],
    ["python", "extract_wolong_summary.py"],
]

for cmd in commands:
    print("\n" + "=" * 70)
    print("RUN:", " ".join(cmd))
    print("=" * 70)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    print(f"[exit_code] {proc.returncode}")
