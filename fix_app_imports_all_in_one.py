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

backup_path = Path("qianqiu_os/app.py.bak_fix_imports_all_in_one")
shutil.copy2(app_path, backup_path)

text = app_path.read_text(encoding="utf-8")

# --------------------------------------------------
# 1) 先做明确路径替换
# --------------------------------------------------
direct_replacements = {
    "from qianqiu_os.adapters.input_adapter import InputAdapter":
        "from qianqiu_os.services.input_adapter import InputAdapter",

    "from qianqiu_os.adapters.output_adapter import OutputAdapter":
        "from qianqiu_os.services.output_adapter import OutputAdapter",

    "from qianqiu_os.agents.agent_loader import AgentLoader":
        "from qianqiu_os.services.agent_loader import AgentLoader",

    "from qianqiu_os.core.scheduler import Scheduler":
        "from qianqiu_os.services.scheduler import Scheduler",

    "from qianqiu_os.core.state_manager import StateManager":
        "from qianqiu_os.services.state_manager import StateManager",

    "from qianqiu_os.core.memory_manager import MemoryManager":
        "from qianqiu_os.services.memory_manager import MemoryManager",

    "from qianqiu_os.core.planner import Planner":
        "from qianqiu_os.services.planner import Planner",

    "from qianqiu_os.core.critic import Critic":
        "from qianqiu_os.services.critic import Critic",

    "from qianqiu_os.core.execution_manager import ExecutionManager":
        "from qianqiu_os.services.execution_manager import ExecutionManager",

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

    "from qianqiu_os.core.metrics_manager import MetricsManager":
        "from qianqiu_os.services.metrics_manager import MetricsManager",

    "from qianqiu_os.core.self_healing_manager import SelfHealingManager":
        "from qianqiu_os.services.self_healing_manager import SelfHealingManager",

    "from qianqiu_os.core.test_manager import TestManager":
        "from qianqiu_os.services.test_manager import TestManager",

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
}

for old, new in direct_replacements.items():
    if old in text:
        text = text.replace(old, new)

# --------------------------------------------------
# 2) 处理不存在模块：experience_manager
# --------------------------------------------------
experience_old = "from qianqiu_os.core.experience_manager import find_similar_experience"
experience_new = """def find_similar_experience(input_payload, tool_result):
    return {
        "matched_count": 0,
        "latest_decision": None,
        "latest_note": None,
    }"""
if experience_old in text:
    text = text.replace(experience_old, experience_new)

# --------------------------------------------------
# 3) 处理不存在模块：platform_governance
# --------------------------------------------------
gov_old = "from qianqiu_os.governance.platform_governance import build_platform_governance"
gov_new = """def build_platform_governance(result):
    tool_result = result.get("tool_result", {}) or {}
    wolong_result = result.get("wolong_result", {}) or {}

    manual_review_required = False
    governance_notes = []

    if tool_result.get("manual_review_required"):
        manual_review_required = True
        governance_notes.append("Tool result requires manual review.")

    if wolong_result.get("manual_review_result", {}).get("manual_review_required"):
        manual_review_required = True
        governance_notes.append("Wolong preliminary review requires human confirmation.")

    return {
        "manual_review_required": manual_review_required,
        "governance_notes": governance_notes,
    }"""
if gov_old in text:
    text = text.replace(gov_old, gov_new)

# --------------------------------------------------
# 4) 处理不存在模块：governance.audit_logger
# --------------------------------------------------
audit_old = "from qianqiu_os.governance.audit_logger import get_audit_logger"
audit_new = """import logging

def get_audit_logger():
    logger = logging.getLogger("qianqiu_os_audit")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger"""
if audit_old in text:
    text = text.replace(audit_old, audit_new)

# --------------------------------------------------
# 5) 如果还有少量老路径，继续兜底替换
# --------------------------------------------------
generic_rules = [
    (r"from qianqiu_os\.core\.([a-zA-Z_][a-zA-Z0-9_]*) import", r"from qianqiu_os.services.\1 import"),
    (r"from qianqiu_os\.adapters\.([a-zA-Z_][a-zA-Z0-9_]*) import", r"from qianqiu_os.services.\1 import"),
]
for pattern, repl in generic_rules:
    text = re.sub(pattern, repl, text)

# registry 单独纠正
text = re.sub(
    r"from qianqiu_os\.services\.agent_registry import",
    "from qianqiu_os.registry.agent_registry import",
    text,
)
text = re.sub(
    r"from qianqiu_os\.services\.tool_registry import",
    "from qianqiu_os.registry.tool_registry import",
    text,
)

app_path.write_text(text, encoding="utf-8")

print(f"[OK] 已写回: {app_path}")
print(f"[OK] 备份文件: {backup_path}")

# --------------------------------------------------
# 6) 打印剩余可疑导入
# --------------------------------------------------
final_text = app_path.read_text(encoding="utf-8")
suspicious = re.findall(
    r"^from\s+qianqiu_os\.(?:core|governance|adapters)\.[^\n]+",
    final_text,
    flags=re.MULTILINE,
)

print("\n=== 剩余可疑旧导入 ===")
if suspicious:
    for item in suspicious:
        print(item)
else:
    print("[OK] 已无 core / governance / adapters 残留导入")

# --------------------------------------------------
# 7) 自动验证
# --------------------------------------------------
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
