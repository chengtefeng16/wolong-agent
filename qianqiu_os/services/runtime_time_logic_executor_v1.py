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

BASE_DIR = Path(__file__).resolve().parents[1]
STATUS_PATH = BASE_DIR / "runtime_governance" / "time_logic" / "time_logic_status_v1.json"
SUMMARY_MD_PATH = BASE_DIR / "project_memory" / "TIME_LOGIC_EXECUTION_SUMMARY_20260314.md"


class RuntimeTimeLogicExecutorV1:
    def _now(self):
        return datetime.now()

    def _now_str(self):
        return self._now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_text(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self):
        now = self._now()
        weekday = now.weekday()  # Monday=0, Friday=4
        current_time = now.strftime("%H:%M:%S")

        daily_night_summary = {
            "time": "23:00",
            "timezone": "Asia/Shanghai",
            "action": "回读当天 constitution/checkpoint/handoff/markdown 更新，生成夜间收口摘要与次日计划",
            "status": "scheduled",
        }

        morning_start_check = {
            "time": "开工前",
            "timezone": "Asia/Shanghai",
            "action": "优先查看前一晚夜间收口摘要、PROJECT_CHECKPOINT、CURRENT_HANDOFF、主宪法文件",
            "status": "scheduled",
        }

        weekly_report_delivery = {
            "time": "Friday 17:00",
            "timezone": "Asia/Shanghai",
            "action": "交付两份正式总表（Word + PDF）",
            "status": "today_due" if weekday == 4 else "scheduled",
        }

        window_handoff = {
            "trigger": "对话过长 / 页面卡顿 / 准备切换新窗口",
            "action": "生成承上启下续接备忘",
            "status": "always_required",
        }

        next_priority_actions = [
            "优先检查主线是否跑偏",
            "优先检查 WhatsApp 真接入是否恢复可推进",
            "优先继续补齐未稳主干",
            "关键节点先固化、先备份、再继续开发",
        ]

        result = {
            "generated_at": self._now_str(),
            "timezone": "Asia/Shanghai",
            "current_weekday": weekday,
            "current_time": current_time,
            "daily_night_summary": daily_night_summary,
            "morning_start_check": morning_start_check,
            "weekly_report_delivery": weekly_report_delivery,
            "window_handoff": window_handoff,
            "next_priority_actions": next_priority_actions,
            "conclusion": "时间逻辑层已从静态规则推进为可落盘执行状态骨架。",
        }

        md = f"""# TIME LOGIC EXECUTION SUMMARY · 2026-03-14

## 一、生成时间
- {result["generated_at"]}

## 二、每日 23:00 固定动作
- 时间：{daily_night_summary["time"]} ({daily_night_summary["timezone"]})
- 动作：{daily_night_summary["action"]}
- 状态：{daily_night_summary["status"]}

## 三、每日开工前固定动作
- 时间：{morning_start_check["time"]} ({morning_start_check["timezone"]})
- 动作：{morning_start_check["action"]}
- 状态：{morning_start_check["status"]}

## 四、每周五 17:00 固定动作
- 时间：{weekly_report_delivery["time"]} ({weekly_report_delivery["timezone"]})
- 动作：{weekly_report_delivery["action"]}
- 状态：{weekly_report_delivery["status"]}

## 五、换窗 / 卡顿 固定动作
- 触发条件：{window_handoff["trigger"]}
- 动作：{window_handoff["action"]}
- 状态：{window_handoff["status"]}

## 六、当前下一优先动作
""" + "\n".join([f"- {x}" for x in next_priority_actions]) + f"""

## 七、结论
{result["conclusion"]}
"""

        self._write_json(STATUS_PATH, result)
        self._write_text(SUMMARY_MD_PATH, md)
        return result


if __name__ == "__main__":
    executor = RuntimeTimeLogicExecutorV1()
    print(json.dumps(executor.build(), ensure_ascii=False, indent=2))
