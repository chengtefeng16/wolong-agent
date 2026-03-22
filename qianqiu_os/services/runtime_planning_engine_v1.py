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

from qianqiu_os.services.runtime_direction_check_v1 import RuntimeDirectionCheckV1
from qianqiu_os.services.runtime_reflection_check_v1 import RuntimeReflectionCheckV1
from qianqiu_os.services.runtime_time_logic_executor_v1 import RuntimeTimeLogicExecutorV1

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "planning" / "planning_engine_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "PLANNING_ENGINE_SUMMARY_20260314.md"

class RuntimePlanningEngineV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_text(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self):
        direction = RuntimeDirectionCheckV1().build()
        reflection = RuntimeReflectionCheckV1().run()
        time_logic = RuntimeTimeLogicExecutorV1().build()

        prioritized_actions = [
            "优先继续推进 WhatsApp 真接入主线",
            "优先在关键节点做六要素备份与主记忆固化",
            "优先按 nightly check / 方向检查 / 时间逻辑保持主线不跑偏",
            "对弱相关主干持续做统一回归，保持稳态",
        ]

        result = {
            "generated_at": self._now_str(),
            "direction_status": direction.get("current_judgement", {}).get("direction_status"),
            "reflection_notes": reflection.get("reflection_notes", []),
            "time_logic_next_priority_actions": time_logic.get("next_priority_actions", []),
            "prioritized_actions": prioritized_actions,
            "conclusion": "推理规划层已具备方向检查、反思结果、时间逻辑三者合并后的最小规划能力。",
        }

        md = f"""# PLANNING ENGINE SUMMARY · 2026-03-14

- 生成时间：{result["generated_at"]}
- direction_status: {result["direction_status"]}

## Reflection Notes
""" + "\n".join([f"- {x}" for x in result["reflection_notes"]]) + f"""

## Time Logic Priority
""" + "\n".join([f"- {x}" for x in result["time_logic_next_priority_actions"]]) + f"""

## Prioritized Actions
""" + "\n".join([f"- {x}" for x in prioritized_actions]) + f"""

## 结论
{result["conclusion"]}
"""
        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, md)
        return result

if __name__ == "__main__":
    print(json.dumps(RuntimePlanningEngineV1().build(), ensure_ascii=False, indent=2))
