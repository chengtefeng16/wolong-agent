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
import ssl
import urllib.request
import urllib.error
from datetime import date, datetime, UTC
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DISCOVERY_RUNS_DIR = BASE / "discovery_runs"
SNAPSHOTS_DIR = BASE / "source_snapshots"

TIMEOUT = 8
USER_AGENT = "Mozilla/5.0 (compatible; WolongDeepFetcher/0.1; +https://example.local)"
MAX_LINKS_PER_SITE = 3

def latest_site_search_run() -> Path:
    files = sorted(DISCOVERY_RUNS_DIR.glob("site_search_run_*.json"))
    if not files:
        raise SystemExit(f"[ERROR] no site_search_run found in {DISCOVERY_RUNS_DIR}")
    return files[-1]

def safe_slug(text: str) -> str:
    return (
        text.lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace(":", "_")
        .replace(" ", "_")
        [:180]
    )

def infer_ext(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    lower_url = url.lower()
    if lower_url.endswith(".pdf") or "pdf" in ct:
        return ".pdf"
    if "html" in ct:
        return ".html"
    if "json" in ct:
        return ".json"
    if "xml" in ct:
        return ".xml"
    if "text" in ct:
        return ".txt"
    return ".bin"

def _do_fetch(url: str, context: ssl.SSLContext, mode: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=context) as resp:
            body = resp.read()
            headers = dict(resp.headers.items())
            return body, {
                "ok": True,
                "status": getattr(resp, "status", 200),
                "final_url": resp.geturl(),
                "content_type": headers.get("Content-Type", ""),
                "content_length": len(body),
                "headers": headers,
                "error": "",
                "fetch_mode": mode,
            }
    except urllib.error.HTTPError as e:
        return None, {
            "ok": False,
            "status": e.code,
            "final_url": url,
            "content_type": "",
            "content_length": 0,
            "headers": dict(getattr(e, "headers", {}).items()) if getattr(e, "headers", None) else {},
            "error": f"HTTPError: {e}",
            "fetch_mode": mode,
        }
    except urllib.error.URLError as e:
        return None, {
            "ok": False,
            "status": 0,
            "final_url": url,
            "content_type": "",
            "content_length": 0,
            "headers": {},
            "error": f"URLError: {e}",
            "fetch_mode": mode,
        }
    except Exception as e:
        return None, {
            "ok": False,
            "status": 0,
            "final_url": url,
            "content_type": "",
            "content_length": 0,
            "headers": {},
            "error": f"Exception: {e}",
            "fetch_mode": mode,
        }

def fetch_url(url: str):
    std_context = ssl.create_default_context()
    body, meta = _do_fetch(url, std_context, "standard_ssl")
    if meta["ok"]:
        return body, meta

    error_text = meta.get("error", "")
    needs_fallback = any(token in error_text for token in [
        "CERTIFICATE_VERIFY_FAILED",
        "self-signed certificate",
        "unable to get local issuer certificate",
        "UNEXPECTED_EOF_WHILE_READING",
        "handshake operation timed out",
    ])
    if not needs_fallback:
        return body, meta

    fallback_context = ssl._create_unverified_context()
    body2, meta2 = _do_fetch(url, fallback_context, "fallback_unverified_ssl")
    if meta2["ok"]:
        meta2["fallback_reason"] = error_text
        meta2["security_note"] = "Fetched via unverified SSL fallback; content should be treated as fetched_with_warning."
        return body2, meta2

    meta2["fallback_reason"] = error_text
    meta2["security_note"] = "Standard and fallback SSL fetch both failed."
    return body2, meta2

def choose_links(item: dict):
    links = item.get("top_links", []) or []
    chosen = []
    seen = set()
    for link in links:
        url = link.get("url", "")
        score = int(link.get("score", 0))
        if not url or score <= 0:
            continue
        if url in seen:
            continue
        seen.add(url)
        chosen.append(link)
        if len(chosen) >= MAX_LINKS_PER_SITE:
            break
    return chosen

def write_snapshot(country_slug: str, domain: str, url: str, body, meta: dict, run_date: str):
    target_dir = SNAPSHOTS_DIR / "deep_links" / run_date / country_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = infer_ext(meta.get("content_type", ""), url)
    base_name = safe_slug(url)

    body_path = target_dir / f"{base_name}{ext}"
    meta_path = target_dir / f"{base_name}.meta.json"

    if body is not None:
        body_path.write_bytes(body)

    meta_payload = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "domain": domain,
        "request_url": url,
        **meta,
        "body_file": body_path.name if body is not None else "",
    }
    meta_path.write_text(json.dumps(meta_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "url": url,
        "domain": domain,
        "ok": meta["ok"],
        "status": meta["status"],
        "content_type": meta["content_type"],
        "content_length": meta["content_length"],
        "body_file": body_path.name if body is not None else "",
        "meta_file": meta_path.name,
        "error": meta["error"],
        "fetch_mode": meta.get("fetch_mode", ""),
        "fallback_reason": meta.get("fallback_reason", ""),
        "security_note": meta.get("security_note", ""),
    }

def build_payload(search_data: dict):
    run_date = date.today().isoformat()
    results = []

    for item in search_data.get("results", []):
        country_slug = item.get("country_slug", "")
        domain = item.get("domain", "")
        chosen = choose_links(item)

        fetched = []
        for link in chosen:
            url = link["url"]
            body, meta = fetch_url(url)
            saved = write_snapshot(country_slug, domain, url, body, meta, run_date)
            saved["score"] = link.get("score", 0)
            saved["keyword_hits"] = link.get("keyword_hits", [])
            fetched.append(saved)

        results.append({
            "country_slug": country_slug,
            "domain": domain,
            "candidate_count": len(item.get("top_links", []) or []),
            "selected_count": len(chosen),
            "fetched_count": len(fetched),
            "items": fetched,
        })

    total_selected = sum(x["selected_count"] for x in results)
    ok_count = sum(1 for x in results for i in x["items"] if i["ok"])
    failed_count = sum(1 for x in results for i in x["items"] if not i["ok"])
    pdf_count = sum(1 for x in results for i in x["items"] if (i["body_file"].lower().endswith(".pdf") if i["body_file"] else False))

    return {
        "run_id": f"deep_fetch_run_{run_date}",
        "run_time": run_date,
        "source_site_search_run_id": search_data.get("run_id", ""),
        "site_count": len(results),
        "total_selected_links": total_selected,
        "ok_links": ok_count,
        "failed_links": failed_count,
        "pdf_links": pdf_count,
        "results": results,
    }

def write_outputs(payload: dict):
    json_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.json"
    md_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.md"

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 卧龙 Agent 深链真实抓取结果（V0）",
        "",
        f"- run_id: {payload['run_id']}",
        f"- source_site_search_run_id: {payload['source_site_search_run_id']}",
        f"- site_count: {payload['site_count']}",
        f"- total_selected_links: {payload['total_selected_links']}",
        f"- ok_links: {payload['ok_links']}",
        f"- failed_links: {payload['failed_links']}",
        f"- pdf_links: {payload['pdf_links']}",
        "",
        "## 站点汇总",
        "",
        "| Country Slug | Domain | selected | fetched | ok | failed |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for item in payload["results"]:
        ok_count = sum(1 for x in item["items"] if x["ok"])
        fail_count = sum(1 for x in item["items"] if not x["ok"])
        lines.append(
            f"| {item['country_slug']} | {item['domain']} | {item['selected_count']} | {item['fetched_count']} | {ok_count} | {fail_count} |"
        )

    lines.extend(["", "## 深链明细", ""])
    for item in payload["results"]:
        lines.append(f"### {item['country_slug']} / {item['domain']}")
        lines.append("")
        if not item["items"]:
            lines.append("- none")
            lines.append("")
            continue
        for x in item["items"]:
            lines.append(
                f"- score={x['score']} ok={x['ok']} status={x['status']} "
                f"fetch_mode={x['fetch_mode']} url={x['url']} "
                f"body_file={x['body_file']} keyword_hits={','.join(x['keyword_hits'])}"
            )
        lines.append("")

    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_out, md_out

def _load_json_loose(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(text)
        return obj

def main() -> int:
    search_path = latest_site_search_run()
    search_data = _load_json_loose(search_path)
    payload = build_payload(search_data)
    json_out, md_out = write_outputs(payload)

    print(f"[OK] site_search input = {search_path.name}")
    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total_selected_links = {payload['total_selected_links']}")
    print(f"[OK] ok_links = {payload['ok_links']}")
    print(f"[OK] failed_links = {payload['failed_links']}")
    print(f"[OK] pdf_links = {payload['pdf_links']}")
    for item in payload["results"][:8]:
        print(f"[OK] domain={item['domain']} selected={item['selected_count']} fetched={item['fetched_count']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
