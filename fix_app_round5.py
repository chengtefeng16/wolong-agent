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
import subprocess
import shutil
import sys
import re

app_path = Path("qianqiu_os/app.py")
if not app_path.exists():
    raise SystemExit("[ERROR] 找不到 qianqiu_os/app.py")

backup_path = Path("qianqiu_os/app.py.bak_before_round5")
shutil.copy2(app_path, backup_path)
print(f"[OK] 已备份: {backup_path}")

text = app_path.read_text(encoding="utf-8")

# -------------------------------------------------
# 1) 修正已知错误导入
# -------------------------------------------------
text = text.replace(
    "from qianqiu_os.agents.agent_loader import AgentLoader",
    "from qianqiu_os.services.agent_loader import AgentLoader",
)

# -------------------------------------------------
# 2) 整体重建 dispatch_next_task() 后到 platform_governance 的大块
#    用前后稳定锚点替换，避免再被半截替换切坏
# -------------------------------------------------
start_marker = "        task, result = scheduler.dispatch_next_task()"
end_marker = '        result["platform_governance"] = platform_governance'

start = text.find(start_marker)
end = text.find(end_marker)

if start == -1 or end == -1 or end <= start:
    print("[ERROR] 没找到可替换的大块起止标记。")
    print("start:", start)
    print("end:", end)
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

# -------------------------------------------------
# 3) 写回
# -------------------------------------------------
app_path.write_text(text, encoding="utf-8")
print(f"[OK] 已写回: {app_path}")

# -------------------------------------------------
# 4) 自动验证
# -------------------------------------------------
commands = [
    ["python", "-m", "py_compile", "qianqiu_os/managers/wolong_manager.py"],
    ["python", "-m", "py_compile", "qianqiu_os/app.py", "qianqiu_os/services/output_adapter.py"],
    ["python", "extract_wolong_summary.py"],
]

for cmd in commands:
    print("\\n" + "=" * 70)
    print("RUN:", " ".join(cmd))
    print("=" * 70)
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)

    print(f"[exit_code] {proc.returncode}")
