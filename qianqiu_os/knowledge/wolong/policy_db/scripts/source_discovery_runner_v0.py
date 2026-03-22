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
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WHITELIST_JSON = BASE.parent / "source_whitelist" / "country_official_site_whitelist_v0.json"
DISCOVERY_RUNS_DIR = BASE / "discovery_runs"

def load_whitelist() -> dict:
    if not WHITELIST_JSON.exists():
        raise SystemExit(f"[ERROR] missing whitelist json: {WHITELIST_JSON}")
    return json.loads(WHITELIST_JSON.read_text(encoding="utf-8"))

def build_country_targets(item: dict) -> dict:
    country_name_en = item.get("country_name_en", "")
    country_name_zh = item.get("country_name_zh", "")
    language_family = item.get("language_family", "unknown")
    status = item.get("status", "pending_verification")
    sites = item.get("sites", []) or []

    verified_sites = [s for s in sites if s.get("verified") is True]
    pending_sites = [s for s in sites if not s.get("verified", False)]

    priority_dimensions = []
    for dim in ["customs", "tax_or_revenue", "official_gazette_or_law_db", "transport_or_industry_or_trade", "high_trust_industry_or_embassy"]:
        if any(s.get("dimension") == dim for s in verified_sites):
            priority_dimensions.append(dim)

    return {
        "country_name_en": country_name_en,
        "country_name_zh": country_name_zh,
        "language_family": language_family,
        "whitelist_status": status,
        "verified_site_count": len(verified_sites),
        "pending_site_count": len(pending_sites),
        "priority_dimensions": priority_dimensions,
        "verified_sites": verified_sites,
        "pending_sites": pending_sites,
        "discovery_ready": len(verified_sites) > 0,
    }

def build_run_payload(data: dict) -> dict:
    today = date.today()
    items = data.get("items", []) or []

    targets = [build_country_targets(item) for item in items]
    ready_targets = [t for t in targets if t["discovery_ready"]]
    pending_targets = [t for t in targets if not t["discovery_ready"]]

    payload = {
        "run_id": f"source_discovery_run_{today.isoformat()}",
        "run_time": today.isoformat(),
        "next_small_update_due": str(today + timedelta(days=3)),
        "next_major_update_due": str(today + timedelta(days=7)),
        "total_countries": len(targets),
        "ready_countries": len(ready_targets),
        "pending_countries": len(pending_targets),
        "targets": targets,
        "summary": {
            "ready_country_names": [t["country_name_en"] for t in ready_targets],
            "pending_country_names": [t["country_name_en"] for t in pending_targets],
        }
    }
    return payload

def write_outputs(payload: dict) -> tuple[Path, Path]:
    DISCOVERY_RUNS_DIR.mkdir(parents=True, exist_ok=True)

    json_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.json"
    md_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.md"

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent source discovery 执行清单（V0）",
        "",
        f"- run_id: {payload['run_id']}",
        f"- run_time: {payload['run_time']}",
        f"- 国家总数: {payload['total_countries']}",
        f"- 可直接执行国家数: {payload['ready_countries']}",
        f"- 仍待补白名单国家数: {payload['pending_countries']}",
        f"- next_small_update_due: {payload['next_small_update_due']}",
        f"- next_major_update_due: {payload['next_major_update_due']}",
        "",
        "## 国家执行清单",
        "",
        "| Country | 中文名 | whitelist_status | verified_sites | pending_sites | discovery_ready | priority_dimensions |",
        "|---|---|---|---:|---:|---|---|",
    ]

    for item in payload["targets"]:
        md_lines.append(
            f"| {item['country_name_en']} | {item['country_name_zh']} | {item['whitelist_status']} | "
            f"{item['verified_site_count']} | {item['pending_site_count']} | "
            f"{'Y' if item['discovery_ready'] else 'N'} | "
            f"{', '.join(item['priority_dimensions'])} |"
        )

    md_lines.extend(["", "## 分国家站点清单", ""])
    for item in payload["targets"]:
        md_lines.append(f"### {item['country_name_en']} / {item['country_name_zh']}")
        md_lines.append("")
        md_lines.append(f"- language_family: {item['language_family']}")
        md_lines.append(f"- whitelist_status: {item['whitelist_status']}")
        md_lines.append(f"- discovery_ready: {'Y' if item['discovery_ready'] else 'N'}")
        md_lines.append("")
        md_lines.append("#### verified_sites")
        if item["verified_sites"]:
            for site in item["verified_sites"]:
                md_lines.append(f"- {site.get('domain')} [{site.get('dimension')}]")
        else:
            md_lines.append("- none")
        md_lines.append("")
        md_lines.append("#### pending_sites")
        if item["pending_sites"]:
            for site in item["pending_sites"]:
                md_lines.append(f"- {site.get('domain')} [{site.get('dimension')}]")
        else:
            md_lines.append("- none")
        md_lines.append("")

    md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return json_out, md_out

def main() -> int:
    data = load_whitelist()
    payload = build_run_payload(data)
    json_out, md_out = write_outputs(payload)

    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total_countries = {payload['total_countries']}")
    print(f"[OK] ready_countries = {payload['ready_countries']}")
    print(f"[OK] pending_countries = {payload['pending_countries']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
