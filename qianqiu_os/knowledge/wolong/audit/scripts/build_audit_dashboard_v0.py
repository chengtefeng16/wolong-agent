# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
COUNTRY_CARDS = BASE / "policy_db" / "country_cards"
GENERATED_OUTPUTS = BASE / "policy_db" / "generated_outputs"
DASHBOARD_DIR = BASE / "audit" / "dashboard"

def priority_bucket(audit_status: str, cross_validation_status: str) -> str:
    if audit_status == "audit_fail":
        return "P0"
    if audit_status == "audit_restricted" and cross_validation_status == "weak":
        return "P1"
    if audit_status == "audit_restricted":
        return "P2"
    if audit_status == "audit_pass_with_warning":
        return "P3"
    return "P4"

def load_country_cards() -> list[dict]:
    rows = []
    for path in sorted(COUNTRY_CARDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))

        audit_status = card.get("audit_status", "audit_fail")
        audit_summary = card.get("audit_summary", {}) or {}
        source_validation_summary = card.get("source_validation_summary", {}) or {}
        source_records = card.get("source_records", []) or []

        cross_validation_status = source_validation_summary.get("cross_validation_status", "weak")
        cross_validation_score = source_validation_summary.get("cross_validation_score", 0)

        row = {
            "country_name_en": card.get("country_name_en", ""),
            "country_name_zh": card.get("country_name_zh", ""),
            "audit_status": audit_status,
            "human_review_needed": bool(audit_summary.get("human_review_needed", False)),
            "cross_validation_status": cross_validation_status,
            "cross_validation_score": cross_validation_score,
            "issues_count": len(audit_summary.get("issues", []) or []),
            "warnings_count": len(audit_summary.get("warnings", []) or []),
            "source_count": len(source_records),
            "last_checked_at": card.get("last_checked_at", ""),
            "next_small_update_due": card.get("next_small_update_due", ""),
            "next_major_update_due": card.get("next_major_update_due", ""),
        }
        row["priority_bucket"] = priority_bucket(
            row["audit_status"],
            row["cross_validation_status"],
        )
        rows.append(row)

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    rows.sort(key=lambda x: (
        order.get(x["priority_bucket"], 9),
        x["country_name_en"]
    ))
    return rows

def build_summary(rows: list[dict]) -> dict:
    summary = {
        "total_countries": len(rows),
        "audit_status_counts": {},
        "priority_bucket_counts": {},
        "human_review_needed_count": 0,
    }

    for row in rows:
        a = row["audit_status"]
        p = row["priority_bucket"]
        summary["audit_status_counts"][a] = summary["audit_status_counts"].get(a, 0) + 1
        summary["priority_bucket_counts"][p] = summary["priority_bucket_counts"].get(p, 0) + 1
        if row["human_review_needed"]:
            summary["human_review_needed_count"] += 1

    return summary

def main() -> int:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_country_cards()
    summary = build_summary(rows)

    out = {
        "summary": summary,
        "rows": rows,
    }

    json_out = DASHBOARD_DIR / "audit_dashboard_v0.json"
    md_out = DASHBOARD_DIR / "audit_dashboard_v0.md"

    json_out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 批量国家审计结果汇总面板（V0）",
        "",
        f"- 国家总数：{summary['total_countries']}",
        f"- 需要人工复核：{summary['human_review_needed_count']}",
        f"- audit_status 分布：{json.dumps(summary['audit_status_counts'], ensure_ascii=False)}",
        f"- priority_bucket 分布：{json.dumps(summary['priority_bucket_counts'], ensure_ascii=False)}",
        "",
        "## 国家列表",
        "",
        "| Country | 中文名 | audit_status | cross_validation | issues | warnings | source_count | next_small | next_major | priority |",
        "|---|---|---|---|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        md_lines.append(
            f"| {row['country_name_en']} | {row['country_name_zh']} | {row['audit_status']} | "
            f"{row['cross_validation_status']}({row['cross_validation_score']}) | "
            f"{row['issues_count']} | {row['warnings_count']} | {row['source_count']} | "
            f"{row['next_small_update_due']} | {row['next_major_update_due']} | {row['priority_bucket']} |"
        )

    md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total countries = {summary['total_countries']}")
    print(f"[OK] audit_status_counts = {summary['audit_status_counts']}")
    print(f"[OK] priority_bucket_counts = {summary['priority_bucket_counts']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
