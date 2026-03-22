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
import re
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = Path(__file__).resolve().parents[1]
SNAPSHOTS_DIR = BASE / "source_snapshots"
DISCOVERY_RUNS_DIR = BASE / "discovery_runs"

KEYWORDS = [
    "import", "vehicle", "used", "customs", "tax", "duty", "tariff", "clearance",
    "regulation", "law", "legal", "gazette", "declaration",
    "aduana", "aduanas", "impuesto", "tribut", "economia",
    "douane", "impot", "fiscal", "decret", "journal",
    "zakon", "kodeks", "tamozhn", "nalog",
    "bojxona", "soliq", "lex",
    "ар", "قانون", "جمارك", "ضريبة", "استيراد"
]

HREF_RE = re.compile(r'href=["\\\']([^"\\\']+)["\\\']', re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\\s+")

def latest_snapshot_date_dir() -> Path:
    dates = sorted([p for p in SNAPSHOTS_DIR.iterdir() if p.is_dir()])
    if not dates:
        raise SystemExit(f"[ERROR] no snapshot date dirs in {SNAPSHOTS_DIR}")
    return dates[-1]

def extract_links_from_html(html_text: str, base_url: str) -> list[dict]:
    out = []
    seen = set()

    for match in HREF_RE.finditer(html_text):
        href = unescape(match.group(1).strip())
        if not href:
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.scheme not in {"http", "https"}:
            continue
        key = full.rstrip("/")
        if key in seen:
            continue
        seen.add(key)

        lower = full.lower()
        hit_keywords = [kw for kw in KEYWORDS if kw.lower() in lower]
        out.append({
            "url": full,
            "path": parsed.path or "/",
            "keyword_hits": hit_keywords,
            "score": len(hit_keywords),
        })

    return out

def parse_domain_from_meta(meta_path: Path) -> str:
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return data.get("domain", "")

def load_homepage_html_pairs(snapshot_date_dir: Path) -> list[dict]:
    items = []
    for country_dir in sorted([p for p in snapshot_date_dir.iterdir() if p.is_dir()]):
        for meta_path in sorted(country_dir.glob("*.meta.json")):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            body_file = meta.get("body_file", "")
            if not body_file.endswith(".html"):
                continue
            body_path = country_dir / body_file
            if not body_path.exists():
                continue
            html_text = body_path.read_text(encoding="utf-8", errors="ignore")
            domain = meta.get("domain", "")
            if not domain:
                continue
            items.append({
                "country_slug": country_dir.name,
                "domain": domain,
                "html_path": body_path,
                "meta_path": meta_path,
                "base_url": f"https://{domain}/",
                "html_text": html_text,
            })
    return items

def build_search_payload() -> dict:
    snapshot_date_dir = latest_snapshot_date_dir()
    items = load_homepage_html_pairs(snapshot_date_dir)

    results = []
    total_candidate_links = 0
    total_keyword_hits = 0

    for item in items:
        links = extract_links_from_html(item["html_text"], item["base_url"])
        scored = sorted(links, key=lambda x: (-x["score"], x["url"]))
        top_links = scored[:20]

        total_candidate_links += len(scored)
        total_keyword_hits += sum(1 for x in scored if x["score"] > 0)

        results.append({
            "country_slug": item["country_slug"],
            "domain": item["domain"],
            "html_file": item["html_path"].name,
            "meta_file": item["meta_path"].name,
            "candidate_link_count": len(scored),
            "keyword_hit_link_count": sum(1 for x in scored if x["score"] > 0),
            "top_links": top_links,
        })

    return {
        "run_id": f"site_search_run_{date.today().isoformat()}",
        "run_time": date.today().isoformat(),
        "snapshot_date": snapshot_date_dir.name,
        "site_count": len(results),
        "total_candidate_links": total_candidate_links,
        "total_keyword_hit_links": total_keyword_hits,
        "results": results,
    }

def write_outputs(payload: dict) -> tuple[Path, Path]:
    json_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.json"
    md_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.md"

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

    lines = [
        "# 卧龙 Agent 站内搜索抓取结果（V0）",
        "",
        f"- run_id: {payload['run_id']}",
        f"- run_time: {payload['run_time']}",
        f"- snapshot_date: {payload['snapshot_date']}",
        f"- site_count: {payload['site_count']}",
        f"- total_candidate_links: {payload['total_candidate_links']}",
        f"- total_keyword_hit_links: {payload['total_keyword_hit_links']}",
        "",
        "## 站点汇总",
        "",
        "| Country Slug | Domain | candidate_links | keyword_hit_links |",
        "|---|---|---:|---:|",
    ]

    for item in payload["results"]:
        lines.append(
            f"| {item['country_slug']} | {item['domain']} | {item['candidate_link_count']} | {item['keyword_hit_link_count']} |"
        )

    lines.extend(["", "## 候选链接明细", ""])
    for item in payload["results"]:
        lines.append(f"### {item['country_slug']} / {item['domain']}")
        lines.append("")
        if not item["top_links"]:
            lines.append("- none")
            lines.append("")
            continue
        for link in item["top_links"]:
            lines.append(
                f"- score={link['score']} url={link['url']} keyword_hits={','.join(link['keyword_hits'])}"
            )
        lines.append("")

    md_out.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    return json_out, md_out

def main() -> int:
    payload = build_search_payload()
    json_out, md_out = write_outputs(payload)

    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] site_count = {payload['site_count']}")
    print(f"[OK] total_candidate_links = {payload['total_candidate_links']}")
    print(f"[OK] total_keyword_hit_links = {payload['total_keyword_hit_links']}")
    for item in payload["results"][:8]:
        print(
            f"[OK] domain={item['domain']} candidates={item['candidate_link_count']} hits={item['keyword_hit_link_count']}"
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
