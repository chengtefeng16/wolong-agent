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

from qianqiu_os.services.runtime_time_logic_executor_v1 import RuntimeTimeLogicExecutorV1

BASE_DIR = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "scheduling" / "scheduling_overview_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "SCHEDULING_OVERVIEW_SUMMARY_20260314.md"

class RuntimeSchedulingOverviewV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_text(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self):
        active = self._read_json(ACTIVE_CONFIG_PATH)
        whatsapp_control = active.get("whatsapp_control", {}) or {}
        delegation_policy = active.get("delegation_policy", {}) or {}
        time_logic = RuntimeTimeLogicExecutorV1().build()

        result = {
            "generated_at": self._now_str(),
            "whatsapp_control": whatsapp_control,
            "delegation_policy_keys": sorted(list(delegation_policy.keys())),
            "time_logic_summary": {
                "nightly_status": time_logic.get("daily_night_summary", {}).get("status"),
                "weekly_report_status": time_logic.get("weekly_report_delivery", {}).get("status"),
                "window_handoff_status": time_logic.get("window_handoff", {}).get("status"),
            },
            "conclusion": "调度层已具备配置调度 + 时间调度总览能力。",
        }

        md = f"""# SCHEDULING OVERVIEW SUMMARY · 2026-03-14

- 生成时间：{result["generated_at"]}

## WhatsApp Control
- ingress_mode: {whatsapp_control.get("ingress_mode")}
- auto_reply: {whatsapp_control.get("auto_reply")}
- auto_dispatch: {whatsapp_control.get("auto_dispatch")}

## Delegation Policy Keys
""" + "\n".join([f"- {x}" for x in result["delegation_policy_keys"]]) + f"""

## Time Logic Summary
- nightly_status: {result["time_logic_summary"]["nightly_status"]}
- weekly_report_status: {result["time_logic_summary"]["weekly_report_status"]}
- window_handoff_status: {result["time_logic_summary"]["window_handoff_status"]}

## 结论
{result["conclusion"]}
"""
        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, md)
        return result

if __name__ == "__main__":
    print(json.dumps(RuntimeSchedulingOverviewV1().build(), ensure_ascii=False, indent=2))
