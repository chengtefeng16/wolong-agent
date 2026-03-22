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
import sys

app_path = Path("qianqiu_os/app.py")
backup_restore = Path("qianqiu_os/app.py.bak_fix_round2")
backup_save = Path("qianqiu_os/app.py.bak_before_round3")

if not app_path.exists():
    print("[ERROR] 找不到 qianqiu_os/app.py")
    sys.exit(1)

# 1) 先恢复到 round2 之前的备份版本（这是最稳的）
if backup_restore.exists():
    shutil.copy2(backup_restore, app_path)
    print(f"[OK] 已从备份恢复: {backup_restore} -> {app_path}")
else:
    print(f"[WARN] 未找到备份 {backup_restore}，将直接基于当前 app.py 修复")

# 再存一份本轮修复前备份
shutil.copy2(app_path, backup_save)
print(f"[OK] 已保存本轮前备份: {backup_save}")

text = app_path.read_text(encoding="utf-8")

# 2) 修正导入
import_replacements = {
    "from qianqiu_os.adapters.input_adapter import InputAdapter":
        "from qianqiu_os.services.input_adapter import InputAdapter",
    "from qianqiu_os.adapters.output_adapter import OutputAdapter":
        "from qianqiu_os.services.output_adapter import OutputAdapter",
    "from qianqiu_os.adapters.audit_logger import AuditLogger":
        "from qianqiu_os.services.audit_logger import AuditLogger",
    "from qianqiu_os.adapters.state_manager import StateManager":
        "from qianqiu_os.services.state_manager import StateManager",
    "from qianqiu_os.adapters.memory_manager import MemoryManager":
        "from qianqiu_os.services.memory_manager import MemoryManager",
    "from qianqiu_os.adapters.metrics_manager import MetricsManager":
        "from qianqiu_os.services.metrics_manager import MetricsManager",
    "from qianqiu_os.adapters.scheduler import Scheduler":
        "from qianqiu_os.services.scheduler import Scheduler",
    "from qianqiu_os.adapters.planner import Planner":
        "from qianqiu_os.services.planner import Planner",
    "from qianqiu_os.adapters.agent_loader import AgentLoader":
        "from qianqiu_os.services.agent_loader import AgentLoader",
    "from qianqiu_os.agents.agent_loader import AgentLoader":
        "from qianqiu_os.services.agent_loader import AgentLoader",
    "from qianqiu_os.adapters.critic import Critic":
        "from qianqiu_os.services.critic import Critic",
    "from qianqiu_os.adapters.execution_manager import ExecutionManager":
        "from qianqiu_os.services.execution_manager import ExecutionManager",
    "from qianqiu_os.adapters.promotion_manager import PromotionManager":
        "from qianqiu_os.services.promotion_manager import PromotionManager",
    "from qianqiu_os.adapters.reflection_manager import ReflectionManager":
        "from qianqiu_os.services.reflection_manager import ReflectionManager",
    "from qianqiu_os.adapters.knowledge_graph_manager import KnowledgeGraphManager":
        "from qianqiu_os.services.knowledge_graph_manager import KnowledgeGraphManager",
    "from qianqiu_os.adapters.human_machine_loop_manager import HumanMachineLoopManager":
        "from qianqiu_os.services.human_machine_loop_manager import HumanMachineLoopManager",
    "from qianqiu_os.adapters.early_warning_manager import EarlyWarningManager":
        "from qianqiu_os.services.early_warning_manager import EarlyWarningManager",
    "from qianqiu_os.adapters.self_healing_manager import SelfHealingManager":
        "from qianqiu_os.services.self_healing_manager import SelfHealingManager",
    "from qianqiu_os.adapters.test_manager import TestManager":
        "from qianqiu_os.services.test_manager import TestManager",
    "from qianqiu_os.adapters.agent_registry import AgentRegistry":
        "from qianqiu_os.registry.agent_registry import AgentRegistry",
    "from qianqiu_os.adapters.tool_registry import ToolRegistry":
        "from qianqiu_os.registry.tool_registry import ToolRegistry",
    "from qianqiu_os.tools.policy_check import policy_check_tool":
        "from qianqiu_os.tools.policy_check_tool import policy_check_tool",
}

for old, new in import_replacements.items():
    text = text.replace(old, new)

# 3) 整体替换旧 Wolong 大块
old_block = '''        detection_result = wolong_manager.detect_wolong_inquiry(incoming_input)
        wolong_result = {
            "wolong_linked": False,
            "inquiry_detected": False,
            "policy_check_executed": False,
        }

        if detection_result.get("is_wolong_inquiry"):
            wolong_context = wolong_manager.build_wolong_task_context(
                incoming_input,
                detection_result,
            )
            policy_result = wolong_manager.run_preliminary_policy_check(wolong_context)
            customer_reply_result = wolong_manager.build_customer_reply(
                wolong_context,
                policy_result,
            )
            manual_review_result = wolong_manager.build_manual_review_summary(
                wolong_context,
                policy_result,
            )
            wolong_result = wolong_manager.build_wolong_result(
                wolong_context,
                policy_result,
                customer_reply_result,
                manual_review_result,
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

        result["platform_governance"] = platform_governance'''

new_block = '''        wolong_result = wolong_manager.handle_inquiry(
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

        result["platform_governance"] = platform_governance'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
    print("[OK] 已整体替换旧 Wolong 调用大块")
else:
    print("[WARN] 没找到旧 Wolong 大块，尝试用起止标记修复")
    start_marker = '        detection_result = wolong_manager.detect_wolong_inquiry(incoming_input)'
    end_marker = '        result["platform_governance"] = platform_governance'
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start != -1 and end != -1 and end > start:
        end = end + len(end_marker)
        text = text[:start] + new_block + text[end:]
        print("[OK] 已通过起止标记整体替换 Wolong 大块")
    else:
        print("[ERROR] 旧 Wolong 大块和起止标记都没找到，停止写入")
        sys.exit(1)

app_path.write_text(text, encoding="utf-8")
print(f"[OK] 已写回 {app_path}")

# 4) 自动验证
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
