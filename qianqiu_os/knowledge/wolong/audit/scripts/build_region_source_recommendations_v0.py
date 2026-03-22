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
DASHBOARD_DIR = BASE / "audit" / "dashboard"

INPUT_JSON = DASHBOARD_DIR / "region_source_gap_v0.json"
OUT_JSON = DASHBOARD_DIR / "region_source_recommendations_v0.json"
OUT_MD = DASHBOARD_DIR / "region_source_recommendations_v0.md"

FRIENDLY_LABELS = {
    "customs": "海关来源",
    "tax_or_revenue": "税务/财政来源",
    "transport_or_industry_or_trade": "交通/工业/商务来源",
    "official_gazette_or_law_db": "官方公报/法律数据库来源",
    "high_trust_industry_or_embassy": "高可信行业/使领馆/商务服务来源",
}

SUGGESTION_TEXT = {
    "customs": "优先补海关官网、海关公告、清关规则页",
    "tax_or_revenue": "优先补税务、财政、收入主管部门资料",
    "transport_or_industry_or_trade": "优先补交通、工业、商务主管部门资料",
    "official_gazette_or_law_db": "优先补官方公报、法令库、官方法规数据库",
    "high_trust_industry_or_embassy": "优先补高可信行业机构、使领馆、商务服务说明",
}

def main() -> int:
    if not INPUT_JSON.exists():
        raise SystemExit(f"[ERROR] missing input: {INPUT_JSON}")

    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    regions = data.get("regions", [])

    recommendations = []
    for region in regions:
        region_pack = region["region_pack"]
        priority_gaps = region.get("priority_source_gaps", [])
        top3 = priority_gaps[:3]

        actions = []
        for idx, gap in enumerate(top3, start=1):
            actions.append({
                "rank": idx,
                "source_dimension": gap,
                "source_dimension_label": FRIENDLY_LABELS.get(gap, gap),
                "action": SUGGESTION_TEXT.get(gap, f"优先补 {gap}"),
            })

        recommendations.append({
            "region_pack": region_pack,
            "country_count": region.get("country_count", 0),
            "audit_restricted_count": region.get("audit_restricted_count", 0),
            "cross_validation_weak_count": region.get("cross_validation_weak_count", 0),
            "priority_source_gaps": top3,
            "actions": actions,
        })

    out = {
        "total_regions": len(recommendations),
        "recommendations": recommendations,
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 区域补源建议（V0）",
        "",
        f"- 区域总数：{out['total_regions']}",
        "",
        "## 区域补源建议概览",
        "",
        "| Region | Countries | Audit Restricted | Weak Cross Validation | Top Priority Sources |",
        "|---|---:|---:|---:|---|",
    ]

    for item in recommendations:
        md_lines.append(
            f"| {item['region_pack']} | {item['country_count']} | "
            f"{item['audit_restricted_count']} | {item['cross_validation_weak_count']} | "
            f"{', '.join(item['priority_source_gaps'])} |"
        )

    md_lines.extend(["", "## 分区域建议", ""])
    for item in recommendations:
        md_lines.append(f"### {item['region_pack']}")
        md_lines.append("")
        for action in item["actions"]:
            md_lines.append(
                f"{action['rank']}. {action['source_dimension_label']}：{action['action']}"
            )
        md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {OUT_JSON.name}")
    print(f"[OK] wrote {OUT_MD.name}")
    for item in recommendations:
        print(
            f"[OK] region={item['region_pack']} top3={item['priority_source_gaps']}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
