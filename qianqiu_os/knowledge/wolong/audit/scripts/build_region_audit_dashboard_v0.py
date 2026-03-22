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
DASHBOARD_DIR = BASE / "audit" / "dashboard"

def load_country_cards() -> list[dict]:
    rows = []
    for path in sorted(COUNTRY_CARDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        audit_summary = card.get("audit_summary", {}) or {}
        source_validation_summary = card.get("source_validation_summary", {}) or {}

        rows.append({
            "country_name_en": card.get("country_name_en", ""),
            "country_name_zh": card.get("country_name_zh", ""),
            "region_pack": card.get("region_pack", "unknown"),
            "audit_status": card.get("audit_status", "audit_fail"),
            "human_review_needed": bool(audit_summary.get("human_review_needed", False)),
            "cross_validation_status": source_validation_summary.get("cross_validation_status", "weak"),
            "cross_validation_score": source_validation_summary.get("cross_validation_score", 0),
            "issues_count": len(audit_summary.get("issues", []) or []),
            "warnings_count": len(audit_summary.get("warnings", []) or []),
            "source_count": len(card.get("source_records", []) or []),
            "next_small_update_due": card.get("next_small_update_due", ""),
            "next_major_update_due": card.get("next_major_update_due", ""),
        })
    return rows

def bucket_order(key: str) -> int:
    order = {"audit_fail": 0, "audit_restricted": 1, "audit_pass_with_warning": 2, "audit_pass": 3}
    return order.get(key, 9)

def build_region_summary(rows: list[dict]) -> dict:
    region_map: dict[str, dict] = {}

    for row in rows:
        region = row["region_pack"]
        if region not in region_map:
            region_map[region] = {
                "region_pack": region,
                "country_count": 0,
                "human_review_needed_count": 0,
                "audit_status_counts": {},
                "cross_validation_counts": {},
                "total_source_count": 0,
                "avg_cross_validation_score": 0.0,
                "max_issues_count": 0,
                "max_warnings_count": 0,
                "countries": [],
            }

        entry = region_map[region]
        entry["country_count"] += 1
        entry["total_source_count"] += row["source_count"]
        entry["max_issues_count"] = max(entry["max_issues_count"], row["issues_count"])
        entry["max_warnings_count"] = max(entry["max_warnings_count"], row["warnings_count"])

        if row["human_review_needed"]:
            entry["human_review_needed_count"] += 1

        a = row["audit_status"]
        c = row["cross_validation_status"]
        entry["audit_status_counts"][a] = entry["audit_status_counts"].get(a, 0) + 1
        entry["cross_validation_counts"][c] = entry["cross_validation_counts"].get(c, 0) + 1
        entry["countries"].append(row)

    for region, entry in region_map.items():
        scores = [c["cross_validation_score"] for c in entry["countries"]]
        entry["avg_cross_validation_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0

        worst_audit = sorted(entry["audit_status_counts"].keys(), key=bucket_order)[0] if entry["audit_status_counts"] else "audit_fail"
        entry["region_priority"] = (
            "P0" if worst_audit == "audit_fail"
            else "P1" if worst_audit == "audit_restricted"
            else "P3" if worst_audit == "audit_pass_with_warning"
            else "P4"
        )

    ordered = sorted(region_map.values(), key=lambda x: (x["region_priority"], x["region_pack"]))
    return {
        "total_regions": len(ordered),
        "regions": ordered,
    }

def main() -> int:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_country_cards()
    summary = build_region_summary(rows)

    json_out = DASHBOARD_DIR / "region_audit_dashboard_v0.json"
    md_out = DASHBOARD_DIR / "region_audit_dashboard_v0.md"

    json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 按区域包聚合统计面板（V0）",
        "",
        f"- 区域总数：{summary['total_regions']}",
        "",
        "## 区域概览",
        "",
        "| Region | Countries | Human Review | Avg Cross Validation | Audit Counts | Cross Validation Counts | Priority |",
        "|---|---:|---:|---:|---|---|---|",
    ]

    for region in summary["regions"]:
        md_lines.append(
            f"| {region['region_pack']} | {region['country_count']} | {region['human_review_needed_count']} | "
            f"{region['avg_cross_validation_score']} | "
            f"{json.dumps(region['audit_status_counts'], ensure_ascii=False)} | "
            f"{json.dumps(region['cross_validation_counts'], ensure_ascii=False)} | "
            f"{region['region_priority']} |"
        )

    md_lines.extend(["", "## 区域明细", ""])
    for region in summary["regions"]:
        md_lines.append(f"### {region['region_pack']}")
        md_lines.append("")
        md_lines.append("| Country | 中文名 | audit_status | cross_validation | issues | warnings | source_count | next_small | next_major |")
        md_lines.append("|---|---|---|---|---:|---:|---:|---|---|")
        for row in sorted(region["countries"], key=lambda x: x["country_name_en"]):
            md_lines.append(
                f"| {row['country_name_en']} | {row['country_name_zh']} | {row['audit_status']} | "
                f"{row['cross_validation_status']}({row['cross_validation_score']}) | "
                f"{row['issues_count']} | {row['warnings_count']} | {row['source_count']} | "
                f"{row['next_small_update_due']} | {row['next_major_update_due']} |"
            )
        md_lines.append("")

    md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total regions = {summary['total_regions']}")
    for region in summary["regions"]:
        print(
            f"[OK] region={region['region_pack']} countries={region['country_count']} "
            f"human_review={region['human_review_needed_count']} priority={region['region_priority']}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
