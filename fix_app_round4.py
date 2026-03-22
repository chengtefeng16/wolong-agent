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

# 优先使用这个备份；没有就退回当前文件
candidate_backups = [
    Path("qianqiu_os/app.py.bak_before_round3"),
    Path("qianqiu_os/app.py.bak_fix_round2"),
    Path("qianqiu_os/app.py.bak_fix_wolong_import_and_block"),
]

restore_from = None
for p in candidate_backups:
    if p.exists():
        restore_from = p
        break

if restore_from is not None:
    shutil.copy2(restore_from, app_path)
    print(f"[OK] 已恢复 app.py <- {restore_from}")
else:
    print("[WARN] 没找到可用备份，将直接基于当前 app.py 修复")

backup_now = Path("qianqiu_os/app.py.bak_before_round4")
shutil.copy2(app_path, backup_now)
print(f"[OK] 已备份当前 app.py -> {backup_now}")

text = app_path.read_text(encoding="utf-8")
lines = text.splitlines()

# 先做全局导入修正
replacements = {
    "from qianqiu_os.agents.agent_loader import AgentLoader":
        "from qianqiu_os.services.agent_loader import AgentLoader",
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

text = app_path.read_text(encoding="utf-8")
for old, new in replacements.items():
    text = text.replace(old, new)
lines = text.splitlines()

# 你贴出来的旧 app.py 中，Wolong 块是 194-239 行
start_line = 194
end_line = 239

new_block = [
'        wolong_result = wolong_manager.handle_inquiry(',
'            incoming_input=incoming_input,',
'            user_memory_context=user_memory_context,',
'        )',
'        result["wolong_result"] = wolong_result',
'',
'        platform_governance = build_platform_governance(result)',
'',
'        wolong_manual_review_required = (',
'            result.get("wolong_result", {})',
'            .get("manual_review_result", {})',
'            .get("manual_review_required", False)',
'        )',
'',
'        if wolong_manual_review_required:',
'            platform_governance["manual_review_required"] = True',
'            platform_governance.setdefault("governance_notes", [])',
'            platform_governance["governance_notes"].append(',
'                "Wolong preliminary review requires human confirmation."',
'            )',
'',
'        result["platform_governance"] = platform_governance',
]

if len(lines) < end_line:
    print(f"[ERROR] 当前 app.py 总行数只有 {len(lines)}，不足以替换 194-239。")
    sys.exit(1)

lines = lines[:start_line - 1] + new_block + lines[end_line:]
new_text = "\n".join(lines) + "\n"
app_path.write_text(new_text, encoding="utf-8")
print(f"[OK] 已写回 {app_path}")
print("[OK] 已按固定行号替换 Wolong 大块")

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
