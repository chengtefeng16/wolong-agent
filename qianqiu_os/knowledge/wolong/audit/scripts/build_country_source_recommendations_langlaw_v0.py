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

OUT_JSON = DASHBOARD_DIR / "country_source_recommendations_langlaw_v0.json"
OUT_MD = DASHBOARD_DIR / "country_source_recommendations_langlaw_v0.md"

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

COUNTRY_PROFILES = {
    "Algeria": {
        "language_family": "fr_ar",
        "legal_style": "francophone_gazette_heavy",
        "site_hint": "优先找法语官方公报、法语法令页、法语海关/财政/工业部门页面；阿语可做交叉验证。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Armenia": {
        "language_family": "hy_ru",
        "legal_style": "post_soviet_legal_portal",
        "site_hint": "优先找亚美尼亚政府法律门户、海关、税务、俄语/本国语法规页，必要时看欧亚经济联盟规则。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Kazakhstan": {
        "language_family": "kk_ru",
        "legal_style": "post_soviet_legal_portal",
        "site_hint": "优先找 eGov、Adilet、海关、税务、俄语/哈语法规与政府说明页。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Kyrgyzstan": {
        "language_family": "ky_ru",
        "legal_style": "post_soviet_legal_portal",
        "site_hint": "优先找政府法律库、海关、税务、俄语/本国语法规与政府说明页。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Uzbekistan": {
        "language_family": "uz_ru",
        "legal_style": "legal_portal_plus_agency_pages",
        "site_hint": "优先找 Lex / 政府法律门户、海关、税务、交通/贸易部门页面，乌兹语和俄语并看。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Tajikistan": {
        "language_family": "tg_ru",
        "legal_style": "legal_portal_plus_agency_pages",
        "site_hint": "优先找法律门户、海关、税务及俄语/塔吉克语政府页面。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
    "Turkmenistan": {
        "language_family": "tk_ru",
        "legal_style": "official_portal_limited_visibility",
        "site_hint": "优先找官方政府页、法律公报/法令页、海关说明；公开度不足时再用高可信行业源辅助。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "high_trust_industry_or_embassy",
            "transport_or_industry_or_trade",
        ],
    },
    "Saudi Arabia": {
        "language_family": "ar_en",
        "legal_style": "agency_guidance_plus_regulatory_pages",
        "site_hint": "优先找阿语/英语官方页、ZATCA、标准/交通/商务主管部门页面；法规与行政说明双轨并看。",
        "bias": [
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "official_gazette_or_law_db",
            "high_trust_industry_or_embassy",
        ],
    },
    "United Arab Emirates": {
        "language_family": "ar_en",
        "legal_style": "agency_guidance_plus_customs_pages",
        "site_hint": "优先找阿语/英语官方页、联邦主管部门、Dubai/Abu Dhabi Customs、工业/交通说明页。",
        "bias": [
            "customs",
            "transport_or_industry_or_trade",
            "official_gazette_or_law_db",
            "tax_or_revenue",
            "high_trust_industry_or_embassy",
        ],
    },
    "Ghana": {
        "language_family": "en",
        "legal_style": "agency_guidance_plus_market_info",
        "site_hint": "优先找 Customs/Revenue Authority、交通/贸易主管部门、英文市场准入和高可信商务说明。",
        "bias": [
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
            "official_gazette_or_law_db",
        ],
    },
    "Mexico": {
        "language_family": "es",
        "legal_style": "spanish_tax_customs_legal_bulletin",
        "site_hint": "优先找西语 SAT/Aduanas、Economía、交通主管部门、官方法令公报与法规库。",
        "bias": [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ],
    },
}

GENERIC_TEXT = {
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
    country = row["country_name_en"]
    gaps = row["gap_list"][:]
    profile = COUNTRY_PROFILES.get(country)

    if profile:
        bias = profile["bias"]
    elif row["cross_validation_status"] == "weak":
        bias = [
            "official_gazette_or_law_db",
            "customs",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "high_trust_industry_or_embassy",
        ]
    else:
        bias = [
            "official_gazette_or_law_db",
            "tax_or_revenue",
            "transport_or_industry_or_trade",
            "customs",
            "high_trust_industry_or_embassy",
        ]

    ordered = [k for k in bias if k in gaps]
    ordered.extend([k for k in gaps if k not in ordered])
    return ordered

def action_text(country_name_en: str, gap: str) -> str:
    profile = COUNTRY_PROFILES.get(country_name_en)
    if not profile:
        return GENERIC_TEXT.get(gap, f"优先补 {gap}")
    return f"{GENERIC_TEXT.get(gap, f'优先补 {gap}')}；{profile['site_hint']}"

def build_recommendations(rows: list[dict]) -> dict:
    recs = []
    for row in rows:
        ordered_gaps = recommend_gaps(row)
        top3 = ordered_gaps[:3]
        profile = COUNTRY_PROFILES.get(row["country_name_en"], {})

        actions = []
        for idx, gap in enumerate(top3, start=1):
            actions.append({
                "rank": idx,
                "source_dimension": gap,
                "source_dimension_label": FRIENDLY_LABELS.get(gap, gap),
                "action": action_text(row["country_name_en"], gap),
            })

        recs.append({
            "country_name_en": row["country_name_en"],
            "country_name_zh": row["country_name_zh"],
            "region_pack": row["region_pack"],
            "audit_status": row["audit_status"],
            "cross_validation_status": row["cross_validation_status"],
            "cross_validation_score": row["cross_validation_score"],
            "human_review_needed": row["human_review_needed"],
            "language_family": profile.get("language_family", "generic"),
            "legal_style": profile.get("legal_style", "generic"),
            "site_hint": profile.get("site_hint", "优先结合官方语言、官方公报、海关和主管部门页面补源。"),
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
        "# 卧龙 Agent 按国家语言/法系差异调整补源建议（V0）",
        "",
        f"- 国家总数：{out['total_countries']}",
        "",
        "## 单国补源建议概览",
        "",
        "| Country | 中文名 | Region | Language | Legal Style | audit_status | Top Priority Sources |",
        "|---|---|---|---|---|---|---|",
    ]

    for item in out["recommendations"]:
        md_lines.append(
            f"| {item['country_name_en']} | {item['country_name_zh']} | {item['region_pack']} | "
            f"{item['language_family']} | {item['legal_style']} | {item['audit_status']} | "
            f"{', '.join(item['priority_source_gaps'])} |"
        )

    md_lines.extend(["", "## 分国家建议", ""])
    for item in out["recommendations"]:
        md_lines.append(f"### {item['country_name_en']} / {item['country_name_zh']}")
        md_lines.append("")
        md_lines.append(f"- 语言体系：{item['language_family']}")
        md_lines.append(f"- 法系/发布习惯：{item['legal_style']}")
        md_lines.append(f"- 找源提示：{item['site_hint']}")
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
        print(
            f"[OK] country={item['country_name_en']} "
            f"lang={item['language_family']} "
            f"legal={item['legal_style']} "
            f"top3={item['priority_source_gaps']}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
