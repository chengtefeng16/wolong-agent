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
PROJECT_MEMORY_DIR = BASE_DIR / "project_memory"
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "memory" / "memory_index_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "MEMORY_INDEX_SUMMARY_20260314.md"

KEY_FILES = [
    BASE_DIR / "PROJECT_CHECKPOINT.md",
    BASE_DIR / "CURRENT_HANDOFF.md",
    PROJECT_MEMORY_DIR / "PROJECT_CONSTITUTION_MASTER_20260314.md",
    PROJECT_MEMORY_DIR / "PROJECT_MARKDOWN_INDEX_20260314.md",
]

class RuntimeMemoryIndexV1:
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
        md_files = sorted(PROJECT_MEMORY_DIR.glob("*.md"))
        weekly_files = sorted((PROJECT_MEMORY_DIR / "weekly_reports").glob("*.md")) if (PROJECT_MEMORY_DIR / "weekly_reports").exists() else []

        result = {
            "generated_at": self._now_str(),
            "project_memory_file_count": len(md_files),
            "weekly_report_file_count": len(weekly_files),
            "key_files": [str(p) for p in KEY_FILES if p.exists()],
            "project_memory_files": [p.name for p in md_files],
            "weekly_report_files": [p.name for p in weekly_files],
            "conclusion": "记忆层已具备主记忆索引、关键文件索引、周报索引的最小稳定能力。",
        }

        md = [
            "# MEMORY INDEX SUMMARY · 2026-03-14",
            "",
            f"- 生成时间：{result['generated_at']}",
            f"- project_memory 文件数：{result['project_memory_file_count']}",
            f"- weekly_reports 文件数：{result['weekly_report_file_count']}",
            "",
            "## 关键文件",
        ]
        md += [f"- {x}" for x in result["key_files"]]
        md += ["", "## project_memory 文件", *[f"- {x}" for x in result["project_memory_files"]]]
        if result["weekly_report_files"]:
            md += ["", "## weekly_reports 文件", *[f"- {x}" for x in result["weekly_report_files"]]]
        md += ["", "## 结论", result["conclusion"], ""]

        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, "\n".join(md))
        return result

if __name__ == "__main__":
    print(json.dumps(RuntimeMemoryIndexV1().build(), ensure_ascii=False, indent=2))
