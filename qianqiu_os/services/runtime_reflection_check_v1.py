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
import sys
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.runtime_alert_guard_v1 import RuntimeAlertGuardV1
from qianqiu_os.services.runtime_self_heal_guard_v1 import RuntimeSelfHealGuardV1


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_MEMORY_DIR = BASE_DIR / "project_memory"
CHECK_STATUS_PATH = PROJECT_MEMORY_DIR / "CHECK_RUNTIME_STATUS_20260314.json"


class RuntimeReflectionCheckV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run(self):
        alert_guard = RuntimeAlertGuardV1()
        alert_result = alert_guard.evaluate()

        self_heal_guard = RuntimeSelfHealGuardV1()
        self_heal_result = self_heal_guard.run(auto_apply=False)

        reflection_notes = []
        next_actions = []

        if alert_result.get("overall_status") == "healthy":
            reflection_notes.append("当前运行态检查结果健康，未发现明显高风险或中风险问题。")
            next_actions.append("继续保持 readonly 安全基线，避免未完成真实接入前误开自动回复。")
        else:
            reflection_notes.append("当前运行态检查结果存在异常，需要优先处理 alert_result 中的问题。")
            next_actions.append("先处理 active config / runtime view / conversation index / auto reply 等异常项。")

        if self_heal_result.get("actions"):
            reflection_notes.append("当前存在可执行的自愈建议，后续可按需自动应用。")
            next_actions.append("根据自愈建议决定是否执行自动修复。")
        else:
            reflection_notes.append("当前无需执行自愈动作，配置已处于稳定安全状态。")
            next_actions.append("继续把主干偏弱层从半稳推进到稳。")

        status = {
            "checked_at": self._now_str(),
            "check_name": "runtime_reflection_check_v1",
            "alert_result": alert_result,
            "self_heal_result": self_heal_result,
            "reflection_notes": reflection_notes,
            "next_actions": next_actions,
            "tomorrow_plan_seed": [
                "优先补强偏弱主干模块",
                "继续收尾 H5 对接链",
                "保持先检查、再修改、再验证的节奏",
            ],
        }

        self._write_json(CHECK_STATUS_PATH, status)
        return status


if __name__ == "__main__":
    checker = RuntimeReflectionCheckV1()
    print(json.dumps(checker.run(), ensure_ascii=False, indent=2))
