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

COVERAGE_KEYS = [
    "customs",
    "tax_or_revenue",
    "transport_or_industry_or_trade",
    "official_gazette_or_law_db",
    "high_trust_industry_or_embassy",
]

def load_country_cards() -> list[dict]:
    rows = []
    for path in sorted(COUNTRY_CARDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        svs = card.get("source_validation_summary", {}) or {}
        coverage = svs.get("source_coverage", {}) or {}

        rows.append({
            "country_name_en": card.get("country_name_en", ""),
            "country_name_zh": card.get("country_name_zh", ""),
            "region_pack": card.get("region_pack", "unknown"),
            "audit_status": card.get("audit_status", "audit_fail"),
            "cross_validation_status": svs.get("cross_validation_status", "weak"),
            "source_coverage": {k: bool(coverage.get(k, False)) for k in COVERAGE_KEYS},
        })
    return rows

def build_region_gap_summary(rows: list[dict]) -> dict:
    region_map: dict[str, dict] = {}

    for row in rows:
        region = row["region_pack"]
        if region not in region_map:
            region_map[region] = {
                "region_pack": region,
                "country_count": 0,
                "audit_restricted_count": 0,
                "cross_validation_weak_count": 0,
                "coverage_counts": {k: 0 for k in COVERAGE_KEYS},
                "gap_counts": {k: 0 for k in COVERAGE_KEYS},
                "countries": [],
            }

        entry = region_map[region]
        entry["country_count"] += 1

        if row["audit_status"] == "audit_restricted":
            entry["audit_restricted_count"] += 1
        if row["cross_validation_status"] == "weak":
            entry["cross_validation_weak_count"] += 1

        for key in COVERAGE_KEYS:
            if row["source_coverage"].get(key, False):
                entry["coverage_counts"][key] += 1
            else:
                entry["gap_counts"][key] += 1

        entry["countries"].append(row)

    for region, entry in region_map.items():
        priority_sources = sorted(
            COVERAGE_KEYS,
            key=lambda k: (-entry["gap_counts"][k], k)
        )
        entry["priority_source_gaps"] = priority_sources

    ordered = sorted(
        region_map.values(),
        key=lambda x: (
            -x["cross_validation_weak_count"],
            -x["audit_restricted_count"],
            x["region_pack"],
        )
    )
    return {
        "total_regions": len(ordered),
        "regions": ordered,
    }

def main() -> int:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_country_cards()
    summary = build_region_gap_summary(rows)

    json_out = DASHBOARD_DIR / "region_source_gap_v0.json"
    md_out = DASHBOARD_DIR / "region_source_gap_v0.md"

    json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 区域级来源缺口分析（V0）",
        "",
        f"- 区域总数：{summary['total_regions']}",
        "",
        "## 区域概览",
        "",
        "| Region | Countries | Audit Restricted | Cross Validation Weak | Priority Gaps |",
        "|---|---:|---:|---:|---|",
    ]

    for region in summary["regions"]:
        md_lines.append(
            f"| {region['region_pack']} | {region['country_count']} | "
            f"{region['audit_restricted_count']} | {region['cross_validation_weak_count']} | "
            f"{', '.join(region['priority_source_gaps'][:3])} |"
        )

    md_lines.extend(["", "## 区域缺口明细", ""])
    for region in summary["regions"]:
        md_lines.append(f"### {region['region_pack']}")
        md_lines.append("")
        md_lines.append("| Source Dimension | Covered Countries | Gap Countries |")
        md_lines.append("|---|---:|---:|")
        for key in COVERAGE_KEYS:
            md_lines.append(
                f"| {key} | {region['coverage_counts'][key]} | {region['gap_counts'][key]} |"
            )
        md_lines.append("")
        md_lines.append("| Country | 中文名 | audit_status | cross_validation | customs | tax | transport/trade | gazette/law_db | high_trust |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|")
        for row in sorted(region["countries"], key=lambda x: x["country_name_en"]):
            c = row["source_coverage"]
            md_lines.append(
                f"| {row['country_name_en']} | {row['country_name_zh']} | {row['audit_status']} | "
                f"{row['cross_validation_status']} | "
                f"{'Y' if c['customs'] else 'N'} | "
                f"{'Y' if c['tax_or_revenue'] else 'N'} | "
                f"{'Y' if c['transport_or_industry_or_trade'] else 'N'} | "
                f"{'Y' if c['official_gazette_or_law_db'] else 'N'} | "
                f"{'Y' if c['high_trust_industry_or_embassy'] else 'N'} |"
            )
        md_lines.append("")

    md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total regions = {summary['total_regions']}")
    for region in summary["regions"]:
        print(
            f"[OK] region={region['region_pack']} "
            f"weak={region['cross_validation_weak_count']} "
            f"priority_gaps={region['priority_source_gaps'][:3]}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
