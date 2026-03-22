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
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DISCOVERY_RUNS_DIR = BASE / "discovery_runs"
SNAPSHOTS_DIR = BASE / "source_snapshots" / "deep_links"
COUNTRY_CARDS_DIR = BASE / "country_cards"
GENERATED_OUTPUTS_DIR = BASE / "generated_outputs"
PENDING_DIR = BASE / "pending_verification"
UPDATE_LOGS_DIR = BASE / "update_logs"

COUNTRY_MAP = {
    "algeria": "algeria.json",
    "armenia": "armenia.json",
    "ghana": "ghana.json",
    "kazakhstan": "kazakhstan.json",
    "kyrgyzstan": "kyrgyzstan.json",
    "mexico": "mexico.json",
    "saudi_arabia": "saudi_arabia.json",
    "tajikistan": "tajikistan.json",
    "turkmenistan": "turkmenistan.json",
    "united_arab_emirates": "united_arab_emirates.json",
    "uzbekistan": "uzbekistan.json",
}

KEY_PATTERNS = {
    "used_vehicle_import_allowed": [
        r"used vehicle",
        r"import",
        r"customs",
        r"aduana",
        r"aduanas",
        r"douane",
        r"импорт",
        r"ввоз",
        r"استيراد",
    ],
    "tax_rules_present": [
        r"tax",
        r"tariff",
        r"duty",
        r"impuesto",
        r"tribut",
        r"налог",
        r"пошлин",
        r"ضريبة",
        r"رسوم",
    ],
    "legal_basis_present": [
        r"law",
        r"code",
        r"regulation",
        r"decree",
        r"gazette",
        r"ley",
        r"decreto",
        r"kodeks",
        r"закон",
        r"قانون",
        r"مرسوم",
    ],
}

def latest_deep_fetch_run() -> Path:
    files = sorted(DISCOVERY_RUNS_DIR.glob("deep_fetch_run_*.json"))
    if not files:
        raise SystemExit(f"[ERROR] no deep_fetch_run found in {DISCOVERY_RUNS_DIR}")
    return files[-1]

def load_json_loose(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(text)
        return obj

def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    if path.suffix.lower() == ".pdf":
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def detect_flags(text: str) -> dict:
    lower = text.lower()

    hits_import = sum(1 for p in KEY_PATTERNS["used_vehicle_import_allowed"] if re.search(p, lower))
    hits_tax = sum(1 for p in KEY_PATTERNS["tax_rules_present"] if re.search(p, lower))
    hits_legal = sum(1 for p in KEY_PATTERNS["legal_basis_present"] if re.search(p, lower))

    return {
        "used_vehicle_import_allowed": "signal_detected" if hits_import > 0 else "pending_extraction",
        "tax_rules_present": hits_tax > 0,
        "legal_basis_present": hits_legal > 0,
        "signal_scores": {
            "import_signal_count": hits_import,
            "tax_signal_count": hits_tax,
            "legal_signal_count": hits_legal,
        },
    }

def merge_country_results(results: list[dict]) -> dict[str, list[dict]]:
    country_map: dict[str, list[dict]] = defaultdict(list)

    for result in results:
        country_slug = result.get("country_slug", "")
        if not country_slug:
            continue
        for item in result.get("items", []) or []:
            if not item.get("ok"):
                continue
            country_map[country_slug].append(item)

    merged: dict[str, list[dict]] = {}
    for country_slug, items in country_map.items():
        seen = set()
        deduped = []
        for item in items:
            key = (item.get("url", ""), item.get("body_file", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        merged[country_slug] = deduped

    return merged

def build_patch_for_country(country_slug: str, entries: list[dict], run_date: str) -> dict:
    texts = []
    evidence = []

    for item in entries:
        body_file = item.get("body_file", "")
        if not body_file:
            continue

        body_path = SNAPSHOTS_DIR / run_date / country_slug / body_file
        text = read_text_safe(body_path)
        if text:
            texts.append(text[:20000])

        evidence.append({
            "url": item.get("url", ""),
            "body_file": body_file,
            "content_type": item.get("content_type", ""),
            "score": item.get("score", 0),
            "keyword_hits": item.get("keyword_hits", []),
            "fetch_mode": item.get("fetch_mode", ""),
        })

    merged_text = "\n\n".join(texts)
    flags = detect_flags(merged_text)

    return {
        "policy_version": "v0.2-deep-fetch-patch-merged",
        "last_deep_extract_at": run_date,
        "source_evidence": evidence,
        "deep_fetch_summary": {
            "evidence_count": len(evidence),
            "text_source_count": len(texts),
            "merged_country_mode": True,
            **flags["signal_scores"],
        },
        "policy_signals": {
            "used_vehicle_import_allowed": flags["used_vehicle_import_allowed"],
            "tax_rules_present": flags["tax_rules_present"],
            "legal_basis_present": flags["legal_basis_present"],
        },
    }

def merge_patch(card: dict, patch: dict) -> dict:
    card["policy_version"] = patch["policy_version"]
    card["last_deep_extract_at"] = patch["last_deep_extract_at"]
    card["deep_fetch_summary"] = patch["deep_fetch_summary"]
    card["policy_signals"] = patch["policy_signals"]

    existing_sources = card.get("source_records", []) or []

    existing_keys = set()
    for src in existing_sources:
        existing_keys.add((src.get("source_type", ""), src.get("source_url", ""), src.get("body_file", "")))

    new_sources = []
    for ev in patch.get("source_evidence", []):
        candidate = {
            "source_type": "deep_fetch_snapshot",
            "source_url": ev.get("url", ""),
            "body_file": ev.get("body_file", ""),
            "content_type": ev.get("content_type", ""),
            "status": "pending_verification",
        }
        key = (candidate["source_type"], candidate["source_url"], candidate["body_file"])
        if key in existing_keys:
            continue
        existing_keys.add(key)
        new_sources.append(candidate)

    card["source_records"] = existing_sources + new_sources
    return card

def write_outputs(country_slug: str, patch: dict, card: dict, run_date: str):
    GENERATED_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    UPDATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    patch_path = GENERATED_OUTPUTS_DIR / f"{country_slug}_deep_patch_{run_date}.json"
    pending_path = PENDING_DIR / f"{country_slug}_deep_pending_{run_date}.json"
    log_path = UPDATE_LOGS_DIR / f"{country_slug}_deep_extract_{run_date}.json"

    patch_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log_path.write_text(json.dumps({
        "country_slug": country_slug,
        "run_date": run_date,
        "policy_version": patch.get("policy_version"),
        "evidence_count": patch.get("deep_fetch_summary", {}).get("evidence_count", 0),
        "text_source_count": patch.get("deep_fetch_summary", {}).get("text_source_count", 0),
        "merged_country_mode": patch.get("deep_fetch_summary", {}).get("merged_country_mode", False),
        "import_signal_count": patch.get("deep_fetch_summary", {}).get("import_signal_count", 0),
        "tax_signal_count": patch.get("deep_fetch_summary", {}).get("tax_signal_count", 0),
        "legal_signal_count": patch.get("deep_fetch_summary", {}).get("legal_signal_count", 0),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return patch_path, pending_path, log_path

def main() -> int:
    run_path = latest_deep_fetch_run()
    data = load_json_loose(run_path)
    run_date = date.today().isoformat()

    merged_results = merge_country_results(data.get("results", []))

    total_updated = 0
    for country_slug, entries in sorted(merged_results.items()):
        if country_slug not in COUNTRY_MAP:
            continue
        if not entries:
            continue

        card_path = COUNTRY_CARDS_DIR / COUNTRY_MAP[country_slug]
        if not card_path.exists():
            continue

        card = load_json_loose(card_path)
        patch = build_patch_for_country(country_slug, entries, run_date)
        merged_card = merge_patch(card, patch)

        card_path.write_text(json.dumps(merged_card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        patch_path, pending_path, log_path = write_outputs(country_slug, patch, merged_card, run_date)

        print(f"[OK] merged and updated {card_path.name}")
        print(f"[OK] patch => {patch_path.name}")
        print(f"[OK] pending => {pending_path.name}")
        print(f"[OK] log => {log_path.name}")
        total_updated += 1

    print(f"[DONE] total updated country cards = {total_updated}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
