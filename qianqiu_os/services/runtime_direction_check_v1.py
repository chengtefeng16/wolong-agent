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
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "direction_check" / "direction_check_status_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "DIRECTION_CHECK_SUMMARY_20260314.md"


class RuntimeDirectionCheckV1:
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
        check_questions = [
            "我们现在做的这件事，是否仍然服务卧龙Agent这个真实跨境汽车贸易场景？",
            "这次新增的模块，是在增强真实业务能力，还是只是在增加抽象复杂度？",
            "我们是不是还在围绕法规、成本、风控、执行、真实客户场景推进？",
            "现在做的东西，未来是中国车商和海外车商都可能用到的吗？",
            "我们是在让卧龙Agent更接近真实可用，还是只是让系统看起来更完整？",
            "AgentOS 当前的增长，有没有反过来证明卧龙Agent的价值？",
            "今天的推进，是在“卧龙先打穿，底座后放大”这条主线上，还是已经开始跑偏？",
        ]

        current_judgement = {
            "direction_status": "on_track",
            "core_conclusion": "当前方向未跑偏，主线仍然是：卧龙先打穿，底座后放大。",
            "main_value": "我们做的不是普通聊天工具，而是跨境汽车贸易的规则、成本、风控、执行一体化系统。",
            "current_risk": "当前最大未完成项不是抽象层不足，而是真实 WhatsApp 接入闭环尚未完成。",
            "next_focus": "优先继续推进 WhatsApp 真接入；并同步补强与其弱相关但仍未完全稳固的主干。",
        }

        reminders = [
            "先确认方向，再继续开发。",
            "先看主干，再看支节；支节长出来以后要回归主干。",
            "不要只长底座，不长业务价值。",
            "关键节点不仅要总结，还要备份、固化、回头看。",
            "不仅用户提醒助手要学习，助手也要提醒用户一起检查方向。",
        ]

        result = {
            "generated_at": self._now_str(),
            "direction_check_questions": check_questions,
            "current_judgement": current_judgement,
            "reminders": reminders,
            "conclusion": "方向检查机制已从纯文字规则推进到可落盘执行骨架。",
        }

        md = f"""# DIRECTION CHECK SUMMARY · 2026-03-14

## 一、生成时间
- {result["generated_at"]}

## 二、阶段性方向检查问题
""" + "\n".join([f"- {q}" for q in check_questions]) + f"""

## 三、当前判断
- direction_status: {current_judgement["direction_status"]}
- 核心结论：{current_judgement["core_conclusion"]}
- 当前主价值：{current_judgement["main_value"]}
- 当前最大风险：{current_judgement["current_risk"]}
- 下一步重点：{current_judgement["next_focus"]}

## 四、提醒语
""" + "\n".join([f"- {x}" for x in reminders]) + f"""

## 五、结论
{result["conclusion"]}
"""

        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, md)
        return result


if __name__ == "__main__":
    checker = RuntimeDirectionCheckV1()
    print(json.dumps(checker.build(), ensure_ascii=False, indent=2))
