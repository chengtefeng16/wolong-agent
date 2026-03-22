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
import re

app_path = Path("qianqiu_os/app.py")
if not app_path.exists():
    raise SystemExit("[ERROR] 找不到 qianqiu_os/app.py")

backup_path = Path("qianqiu_os/app.py.bak_fix_all_import_paths")
shutil.copy2(app_path, backup_path)

text = app_path.read_text(encoding="utf-8")

replacements = {
    # adapters / agents / core 旧路径统一修正
    "from qianqiu_os.adapters.input_adapter import InputAdapter":
        "from qianqiu_os.services.input_adapter import InputAdapter",

    "from qianqiu_os.agents.agent_loader import AgentLoader":
        "from qianqiu_os.services.agent_loader import AgentLoader",

    "from qianqiu_os.core.critic import Critic":
        "from qianqiu_os.services.critic import Critic",
    "from qianqiu_os.core.scheduler import Scheduler":
        "from qianqiu_os.services.scheduler import Scheduler",
    "from qianqiu_os.core.planner import Planner":
        "from qianqiu_os.services.planner import Planner",
    "from qianqiu_os.core.state_manager import StateManager":
        "from qianqiu_os.services.state_manager import StateManager",
    "from qianqiu_os.core.memory_manager import MemoryManager":
        "from qianqiu_os.services.memory_manager import MemoryManager",
    "from qianqiu_os.core.metrics_manager import MetricsManager":
        "from qianqiu_os.services.metrics_manager import MetricsManager",
    "from qianqiu_os.core.output_adapter import OutputAdapter":
        "from qianqiu_os.services.output_adapter import OutputAdapter",
    "from qianqiu_os.core.execution_manager import ExecutionManager":
        "from qianqiu_os.services.execution_manager import ExecutionManager",
    "from qianqiu_os.core.self_healing_manager import SelfHealingManager":
        "from qianqiu_os.services.self_healing_manager import SelfHealingManager",
    "from qianqiu_os.core.promotion_manager import PromotionManager":
        "from qianqiu_os.services.promotion_manager import PromotionManager",
    "from qianqiu_os.core.reflection_manager import ReflectionManager":
        "from qianqiu_os.services.reflection_manager import ReflectionManager",
    "from qianqiu_os.core.knowledge_graph_manager import KnowledgeGraphManager":
        "from qianqiu_os.services.knowledge_graph_manager import KnowledgeGraphManager",
    "from qianqiu_os.core.human_machine_loop_manager import HumanMachineLoopManager":
        "from qianqiu_os.services.human_machine_loop_manager import HumanMachineLoopManager",
    "from qianqiu_os.core.early_warning_manager import EarlyWarningManager":
        "from qianqiu_os.services.early_warning_manager import EarlyWarningManager",
    "from qianqiu_os.core.test_manager import TestManager":
        "from qianqiu_os.services.test_manager import TestManager",
    "from qianqiu_os.core.audit_logger import AuditLogger":
        "from qianqiu_os.services.audit_logger import AuditLogger",
    "from qianqiu_os.core.api_executor import ApiExecutor":
        "from qianqiu_os.services.api_executor import ApiExecutor",
    "from qianqiu_os.core.browser_executor import BrowserExecutor":
        "from qianqiu_os.services.browser_executor import BrowserExecutor",
    "from qianqiu_os.core.desktop_executor import DesktopExecutor":
        "from qianqiu_os.services.desktop_executor import DesktopExecutor",

    "from qianqiu_os.core.agent_registry import AgentRegistry":
        "from qianqiu_os.registry.agent_registry import AgentRegistry",
    "from qianqiu_os.core.tool_registry import ToolRegistry":
        "from qianqiu_os.registry.tool_registry import ToolRegistry",

    "from qianqiu_os.core.task import Task":
        "from qianqiu_os.models.task import Task",
}

changed = []
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
        changed.append((old, new))

# experience_manager 特殊兜底：项目里没这个文件就内置一个空实现
text2 = re.sub(
    r"from\s+qianqiu_os\.core\.experience_manager\s+import\s+find_similar_experience",
    """try:
    from qianqiu_os.services.experience_manager import find_similar_experience
except Exception:
    def find_similar_experience(input_payload, tool_result):
        return {
            "matched_count": 0,
            "latest_decision": None,
            "latest_note": None,
        }""",
    text,
)
if text2 != text:
    text = text2
    changed.append(("from qianqiu_os.core.experience_manager import find_similar_experience", "fallback stub"))

# 再扫一遍是否还有 qianqiu_os.core 残留
remaining_core = re.findall(
    r"^from\s+qianqiu_os\.core\.[^\n]+",
    text,
    flags=re.MULTILINE
)

app_path.write_text(text, encoding="utf-8")

print("[OK] 已写回 qianqiu_os/app.py")
print(f"[OK] 备份文件: {backup_path}")
print()
print("=== 已替换导入 ===")
if changed:
    for old, new in changed:
        print(f"- {old}")
        print(f"  -> {new}")
else:
    print("[WARN] 这轮没有匹配到需要替换的导入")

print()
print("=== 剩余 core 导入 ===")
if remaining_core:
    for item in remaining_core:
        print(item)
else:
    print("[OK] 已无 qianqiu_os.core 残留导入")

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
