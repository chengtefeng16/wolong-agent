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
if not app_path.exists():
    raise SystemExit("[ERROR] 找不到 qianqiu_os/app.py")

text = app_path.read_text(encoding="utf-8")

marker = "def main():"
idx = text.find(marker)
if idx == -1:
    raise SystemExit("[ERROR] 在 app.py 里找不到 def main()，本次停止，避免误伤")

backup_path = Path("qianqiu_os/app.py.bak_rewrite_header_once")
shutil.copy2(app_path, backup_path)

new_header = '''import logging

from qianqiu_os.services.input_adapter import InputAdapter
from qianqiu_os.services.output_adapter import OutputAdapter
from qianqiu_os.services.agent_loader import AgentLoader
from qianqiu_os.services.scheduler import Scheduler
from qianqiu_os.services.state_manager import StateManager
from qianqiu_os.services.memory_manager import MemoryManager
from qianqiu_os.services.planner import Planner
from qianqiu_os.services.critic import Critic
from qianqiu_os.services.execution_manager import ExecutionManager
from qianqiu_os.services.promotion_manager import PromotionManager
from qianqiu_os.services.reflection_manager import ReflectionManager
from qianqiu_os.services.knowledge_graph_manager import KnowledgeGraphManager
from qianqiu_os.services.human_machine_loop_manager import HumanMachineLoopManager
from qianqiu_os.services.early_warning_manager import EarlyWarningManager
from qianqiu_os.services.metrics_manager import MetricsManager
from qianqiu_os.services.self_healing_manager import SelfHealingManager
from qianqiu_os.services.test_manager import TestManager
from qianqiu_os.registry.agent_registry import AgentRegistry
from qianqiu_os.registry.tool_registry import ToolRegistry
from qianqiu_os.managers.wolong_manager import WolongManager
from qianqiu_os.tools.policy_check_tool import policy_check_tool


def get_audit_logger():
    logger = logging.getLogger("qianqiu_os_audit")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def find_similar_experience(input_payload, tool_result):
    return {
        "matched_count": 0,
        "latest_decision": None,
        "latest_note": None,
    }


def build_platform_governance(result):
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
    }


ENABLE_REAL_FAILED_STEP_INJECTION = True
ENABLE_TEST_CUT4_CONCURRENCY_BOUNDARY = True
ENABLE_TEST_CUT5_STEP1_REPLAY_METRICS = True
ENABLE_TEST_CUT5_STEP2_REPLAY_ENHANCED = True
ENABLE_TEST_CUT5_STEP3_H5_PANEL_LINKAGE = True


'''

new_text = new_header + text[idx:]
app_path.write_text(new_text, encoding="utf-8")

print(f"[OK] 已整体重写 app.py 文件头")
print(f"[OK] 备份文件: {backup_path}")

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
