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
from collections import Counter
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
AUDIT_DIR = BASE_DIR / "runtime_governance" / "audit_logs"
OUTPUT_JSON_PATH = BASE_DIR / "runtime_governance" / "audit_overview" / "audit_overview_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "RUNTIME_AUDIT_OVERVIEW_SUMMARY_20260314.md"


class RuntimeAuditOverviewV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_text(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self):
        files = sorted(AUDIT_DIR.glob("*.json"))
        records = []

        for path in files:
            data = self._read_json(path)
            if isinstance(data, dict):
                data["_source_file"] = path.name
                records.append(data)

        audit_type_counter = Counter()
        for item in records:
            audit_type_counter[item.get("audit_type", "unknown")] += 1

        recent_items = []
        for item in records[-8:]:
            recent_items.append({
                "audit_type": item.get("audit_type"),
                "saved_at": item.get("saved_at"),
                "operator_id": item.get("operator_id"),
                "operator_name": item.get("operator_name"),
                "change_reason": item.get("change_reason"),
                "_source_file": item.get("_source_file"),
            })

        result = {
            "generated_at": self._now_str(),
            "audit_dir": str(AUDIT_DIR),
            "total_audit_records": len(records),
            "audit_type_counts": dict(audit_type_counter),
            "recent_items": recent_items,
            "conclusion": "反向审计总览层已具备最小汇总能力，可用于关键节点回看保存、回滚、配置变更等历史动作。",
        }

        md_lines = [
            "# RUNTIME AUDIT OVERVIEW SUMMARY · 2026-03-14",
            "",
            "## 一、生成时间",
            f"- {result['generated_at']}",
            "",
            "## 二、审计总览",
            f"- 审计目录：{result['audit_dir']}",
            f"- 审计记录总数：{result['total_audit_records']}",
            "",
            "## 三、审计类型统计",
        ]

        if result["audit_type_counts"]:
            for k, v in result["audit_type_counts"].items():
                md_lines.append(f"- {k}: {v}")
        else:
            md_lines.append("- 当前暂无审计记录")

        md_lines.extend([
            "",
            "## 四、最近审计记录",
        ])

        if recent_items:
            for item in recent_items:
                md_lines.append(
                    f"- [{item.get('saved_at')}] {item.get('audit_type')} / {item.get('operator_id')} / {item.get('change_reason')} / {item.get('_source_file')}"
                )
        else:
            md_lines.append("- 当前暂无最近审计记录")

        md_lines.extend([
            "",
            "## 五、结论",
            result["conclusion"],
            "",
        ])

        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, "\n".join(md_lines))
        return result


if __name__ == "__main__":
    builder = RuntimeAuditOverviewV1()
    print(json.dumps(builder.build(), ensure_ascii=False, indent=2))
