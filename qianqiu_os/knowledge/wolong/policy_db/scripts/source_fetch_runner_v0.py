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
UPDATE_LOGS_DIR = BASE / "update_logs"

USER_AGENT = "Mozilla/5.0 (compatible; WolongSourceFetcher/0.1; +https://example.local)"
TIMEOUT = 20

def latest_discovery_run() -> Path:
    files = sorted(DISCOVERY_RUNS_DIR.glob("source_discovery_run_*.json"))
    if not files:
        raise SystemExit(f"[ERROR] no discovery run found in {DISCOVERY_RUNS_DIR}")
    return files[-1]

def safe_slug(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(":", "_")
    )

def infer_ext(content_type: str) -> str:
    ct = (content_type or "").lower()
    if "html" in ct:
        return ".html"
    if "json" in ct:
        return ".json"
    if "pdf" in ct:
        return ".pdf"
    if "xml" in ct:
        return ".xml"
    if "text" in ct:
        return ".txt"
    return ".bin"

def _do_fetch(url: str, context: ssl.SSLContext, mode: str) -> tuple[bytes | None, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=context) as resp:
            body = resp.read()
            headers = dict(resp.headers.items())
            meta = {
                "ok": True,
                "status": getattr(resp, "status", 200),
                "final_url": resp.geturl(),
                "content_type": headers.get("Content-Type", ""),
                "content_length": len(body),
                "headers": headers,
                "error": "",
                "fetch_mode": mode,
            }
            return body, meta
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

def fetch_url(url: str) -> tuple[bytes | None, dict]:
    # 1) 标准模式
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

    # 2) 受控 fallback：放宽证书校验，仅用于抓取兼容测试
    fallback_context = ssl._create_unverified_context()
    body2, meta2 = _do_fetch(url, fallback_context, "fallback_unverified_ssl")
    if meta2["ok"]:
        meta2["fallback_reason"] = error_text
        meta2["security_note"] = "Fetched via unverified SSL fallback; content should be treated as fetched_with_warning."
        return body2, meta2

    # 3) fallback 也失败，则把两次错误都记录下来
    meta2["fallback_reason"] = error_text
    meta2["security_note"] = "Standard and fallback SSL fetch both failed."
    return body2, meta2

def write_snapshot(country_slug: str, domain: str, body: bytes | None, meta: dict, run_date: str) -> dict:
    target_dir = SNAPSHOTS_DIR / run_date / country_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = infer_ext(meta.get("content_type", ""))
    base_name = f"{safe_slug(domain)}__root"

    body_path = target_dir / f"{base_name}{ext}"
    meta_path = target_dir / f"{base_name}.meta.json"

    if body is not None:
        body_path.write_bytes(body)

    meta_payload = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "domain": domain,
        "request_url": f"https://{domain}/",
        **meta,
        "body_file": body_path.name if body is not None else "",
    }
    meta_path.write_text(json.dumps(meta_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
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

def build_fetch_run(discovery: dict) -> dict:
    run_date = date.today().isoformat()
    results = []

    for country in discovery.get("targets", []):
        country_name_en = country.get("country_name_en", "")
        country_name_zh = country.get("country_name_zh", "")
        country_slug = safe_slug(country_name_en)
        verified_sites = country.get("verified_sites", []) or []

        site_results = []
        for site in verified_sites:
            domain = site.get("domain", "").strip()
            if not domain:
                continue
            url = f"https://{domain}/"
            body, meta = fetch_url(url)
            saved = write_snapshot(country_slug, domain, body, meta, run_date)
            saved["dimension"] = site.get("dimension", "")
            site_results.append(saved)

        results.append({
            "country_name_en": country_name_en,
            "country_name_zh": country_name_zh,
            "verified_site_count": len(verified_sites),
            "fetched_site_count": len(site_results),
            "sites": site_results,
        })

    total_sites = sum(x["verified_site_count"] for x in results)
    ok_sites = sum(1 for x in results for s in x["sites"] if s["ok"])
    failed_sites = sum(1 for x in results for s in x["sites"] if not s["ok"])
    fallback_sites = sum(1 for x in results for s in x["sites"] if s.get("fetch_mode") == "fallback_unverified_ssl" and s["ok"])

    return {
        "run_id": f"source_fetch_run_{run_date}",
        "run_time": run_date,
        "source_discovery_run_id": discovery.get("run_id", ""),
        "country_count": len(results),
        "total_verified_sites": total_sites,
        "ok_sites": ok_sites,
        "failed_sites": failed_sites,
        "fallback_sites": fallback_sites,
        "results": results,
    }

def write_fetch_run(payload: dict) -> tuple[Path, Path]:
    json_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.json"
    md_out = DISCOVERY_RUNS_DIR / f"{payload['run_id']}.md"

    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# 卧龙 Agent 真实网页抓取执行结果（V0.1）",
        "",
        f"- run_id: {payload['run_id']}",
        f"- source_discovery_run_id: {payload['source_discovery_run_id']}",
        f"- country_count: {payload['country_count']}",
        f"- total_verified_sites: {payload['total_verified_sites']}",
        f"- ok_sites: {payload['ok_sites']}",
        f"- failed_sites: {payload['failed_sites']}",
        f"- fallback_sites: {payload['fallback_sites']}",
        "",
        "## 国家抓取结果",
        "",
        "| Country | 中文名 | verified_sites | fetched_sites | ok_sites | failed_sites | fallback_sites |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for country in payload["results"]:
        ok_count = sum(1 for s in country["sites"] if s["ok"])
        fail_count = sum(1 for s in country["sites"] if not s["ok"])
        fallback_count = sum(1 for s in country["sites"] if s.get("fetch_mode") == "fallback_unverified_ssl" and s["ok"])
        md_lines.append(
            f"| {country['country_name_en']} | {country['country_name_zh']} | "
            f"{country['verified_site_count']} | {country['fetched_site_count']} | {ok_count} | {fail_count} | {fallback_count} |"
        )

    md_lines.extend(["", "## 站点明细", ""])
    for country in payload["results"]:
        md_lines.append(f"### {country['country_name_en']} / {country['country_name_zh']}")
        md_lines.append("")
        if not country["sites"]:
            md_lines.append("- none")
            md_lines.append("")
            continue
        for site in country["sites"]:
            md_lines.append(
                f"- {site['domain']} [{site['dimension']}] "
                f"status={site['status']} ok={site['ok']} "
                f"fetch_mode={site['fetch_mode']} "
                f"content_type={site['content_type']} body_file={site['body_file']} "
                f"error={site['error']} fallback_reason={site['fallback_reason']}"
            )
        md_lines.append("")

    md_out.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return json_out, md_out

def main() -> int:
    discovery_path = latest_discovery_run()
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))

    payload = build_fetch_run(discovery)
    json_out, md_out = write_fetch_run(payload)

    print(f"[OK] discovery input = {discovery_path.name}")
    print(f"[OK] wrote {json_out.name}")
    print(f"[OK] wrote {md_out.name}")
    print(f"[OK] total_verified_sites = {payload['total_verified_sites']}")
    print(f"[OK] ok_sites = {payload['ok_sites']}")
    print(f"[OK] failed_sites = {payload['failed_sites']}")
    print(f"[OK] fallback_sites = {payload['fallback_sites']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
