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
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "agent_registry" / "agent_registry_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "AGENT_REGISTRY_SUMMARY_20260314.md"

class RuntimeAgentRegistryV1:
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
        agents = [
            {
                "agent_name": "WolongAgent",
                "domain": "跨境汽车贸易",
                "status": "active_primary",
                "depends_on": ["AgentOS"],
            },
            {
                "agent_name": "AgentOS",
                "domain": "基础底座",
                "status": "foundation_active",
                "depends_on": [],
            },
            {
                "agent_name": "BuddhismAgent",
                "domain": "佛学",
                "status": "planned",
                "depends_on": ["AgentOS"],
            },
            {
                "agent_name": "TCMAgent",
                "domain": "中医",
                "status": "planned",
                "depends_on": ["AgentOS"],
            },
            {
                "agent_name": "LegalAgent",
                "domain": "法律",
                "status": "planned",
                "depends_on": ["AgentOS"],
            },
        ]

        result = {
            "generated_at": self._now_str(),
            "agent_count": len(agents),
            "agents": agents,
            "core_strategy": "卧龙先打穿，底座后放大。",
            "conclusion": "Agent 配置注册层已具备最小注册索引能力。",
        }

        md = f"""# AGENT REGISTRY SUMMARY · 2026-03-14

- 生成时间：{result["generated_at"]}
- agent_count: {result["agent_count"]}
- core_strategy: {result["core_strategy"]}

## Agents
""" + "\n".join([f"- {a['agent_name']} / {a['domain']} / {a['status']} / depends_on={','.join(a['depends_on']) if a['depends_on'] else 'none'}" for a in agents]) + f"""

## 结论
{result["conclusion"]}
"""
        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, md)
        return result

if __name__ == "__main__":
    print(json.dumps(RuntimeAgentRegistryV1().build(), ensure_ascii=False, indent=2))
