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

OUT_JSON = DASHBOARD_DIR / "country_source_recommendations_v0.json"
OUT_MD = DASHBOARD_DIR / "country_source_recommendations_v0.md"

COVERAGE_KEYS = [
    "customs",
    "tax_or_revenue",
    "transport_or_industry_or_trade",
    "official_gazette_or_law_db",
    "high_trust_industry_or_embassy",
]

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

def load_country_cards() -> list[dict]:
    rows = []
    for path in sorted(COUNTRY_CARDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        audit_summary = card.get("audit_summary", {}) or {}
        svs = card.get("source_validation_summary", {}) or {}
        coverage = svs.get("source_coverage", {}) or {}

        source_coverage = {k: bool(coverage.get(k, False)) for k in COVERAGE_KEYS}
        gap_list = [k for k in COVERAGE_KEYS if not source_coverage[k]]

        rows.append({
            "country_name_en": card.get("country_name_en", ""),
            "country_name_zh": card.get("country_name_zh", ""),
            "region_pack": card.get("region_pack", "unknown"),
            "audit_status": card.get("audit_status", "audit_fail"),
            "human_review_needed": bool(audit_summary.get("human_review_needed", False)),
            "cross_validation_status": svs.get("cross_validation_status", "weak"),
            "cross_validation_score": svs.get("cross_validation_score", 0),
            "source_coverage": source_coverage,
            "gap_list": gap_list,
        })
    return rows

def recommend_gaps(row: dict) -> list[str]:
    gaps = row["gap_list"][:]

    if row["cross_validation_status"] == "weak":
        priority_bias = [
            "customs",
            "official_gazette_or_law_db",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ]
    else:
        priority_bias = [
            "official_gazette_or_law_db",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "customs",
            "high_trust_industry_or_embassy",
        ]

    ordered = [k for k in priority_bias if k in gaps]
    ordered.extend([k for k in gaps if k not in ordered])
    return ordered

def build_recommendations(rows: list[dict]) -> dict:
    recs = []
    for row in rows:
        ordered_gaps = recommend_gaps(row)
        top3 = ordered_gaps[:3]

        actions = []
        for idx, gap in enumerate(top3, start=1):
            actions.append({
                "rank": idx,
                "source_dimension": gap,
                "source_dimension_label": FRIENDLY_LABELS.get(gap, gap),
                "action": SUGGESTION_TEXT.get(gap, f"优先补 {gap}"),
            })

        recs.append({
            "country_name_en": row["country_name_en"],
            "country_name_zh": row["country_name_zh"],
            "region_pack": row["region_pack"],
            "audit_status": row["audit_status"],
            "cross_validation_status": row["cross_validation_status"],
            "cross_validation_score": row["cross_validation_score"],
            "human_review_needed": row["human_review_needed"],
            "priority_source_gaps": top3,
            "actions": actions,
        })

    recs.sort(key=lambda x: (
        0 if x["cross_validation_status"] == "weak" else 1,
        x["country_name_en"]
    ))

    return {
        "total_countries": len(recs),
        "recommendations": recs,
    }

def main() -> int:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_country_cards()
    out = build_recommendations(rows)

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 单国补源建议（V0）",
        "",
        f"- 国家总数：{out['total_countries']}",
        "",
        "## 单国补源建议概览",
        "",
        "| Country | 中文名 | Region | audit_status | cross_validation | Top Priority Sources |",
        "|---|---|---|---|---|---|",
    ]

    for item in out["recommendations"]:
        md_lines.append(
            f"| {item['country_name_en']} | {item['country_name_zh']} | {item['region_pack']} | "
            f"{item['audit_status']} | {item['cross_validation_status']}({item['cross_validation_score']}) | "
            f"{', '.join(item['priority_source_gaps'])} |"
        )

    md_lines.extend(["", "## 分国家建议", ""])
    for item in out["recommendations"]:
        md_lines.append(f"### {item['country_name_en']} / {item['country_name_zh']}")
        md_lines.append("")
        for action in item["actions"]:
            md_lines.append(
                f"{action['rank']}. {action['source_dimension_label']}：{action['action']}"
            )
        md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {OUT_JSON.name}")
    print(f"[OK] wrote {OUT_MD.name}")
    print(f"[OK] total countries = {out['total_countries']}")
    for item in out["recommendations"][:5]:
        print(f"[OK] country={item['country_name_en']} top3={item['priority_source_gaps']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
