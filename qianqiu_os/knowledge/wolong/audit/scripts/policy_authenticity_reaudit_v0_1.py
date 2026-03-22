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
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
COUNTRY_CARDS_DIR = BASE / "policy_db" / "country_cards"
GENERATED_OUTPUTS_DIR = BASE / "policy_db" / "generated_outputs"
UPDATE_LOGS_DIR = BASE / "policy_db" / "update_logs"

def load_json_loose(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(text)
        return obj

def classify_cross_validation_status(source_records: list[dict]) -> tuple[str, int]:
    score = 0
    for s in source_records:
        st = (s.get("source_type") or "").lower()
        url = (s.get("source_url") or "").lower()

        if "deep_fetch_snapshot" in st:
            score += 1
        if "official_gazette" in st or "law_db" in st:
            score += 2
        if "customs" in url:
            score += 2
        if "tax" in url or "impuesto" in url or "налог" in url or "ضريبة" in url:
            score += 1
        if url.endswith(".pdf"):
            score += 1

    if score >= 6:
        return "strong", score
    if score >= 4:
        return "medium", score
    return "weak", score

def re_audit_country_card(path: Path) -> dict:
    card = load_json_loose(path)
    source_records = card.get("source_records", []) or []
    deep_summary = card.get("deep_fetch_summary", {}) or {}
    signals = card.get("policy_signals", {}) or {}

    cross_validation_status, score = classify_cross_validation_status(source_records)

    warnings = []
    issues = []

    if deep_summary.get("evidence_count", 0) == 0:
        warnings.append("no_deep_evidence")
    if signals.get("used_vehicle_import_allowed") == "pending_extraction":
        warnings.append("used_vehicle_import_not_extracted")
    if not signals.get("legal_basis_present", False):
        warnings.append("legal_basis_not_detected")
    if not signals.get("tax_rules_present", False):
        warnings.append("tax_rules_not_detected")

    if cross_validation_status == "strong" and len(warnings) <= 1:
        audit_status = "audit_pass_with_warning" if warnings else "audit_pass"
    elif cross_validation_status == "medium":
        audit_status = "audit_pass_with_warning"
    else:
        audit_status = "audit_restricted"

    summary = {
        "country_file": path.name,
        "audit_status": audit_status,
        "cross_validation_status": cross_validation_status,
        "cross_validation_score": score,
        "issues": issues,
        "warnings": warnings,
        "audit_last_checked_at": str(date.today()),
        "deep_fetch_summary": deep_summary,
        "policy_signals": signals,
    }

    card["audit_status"] = audit_status
    card["audit_last_checked_at"] = summary["audit_last_checked_at"]
    card["source_validation_summary"] = {
        "cross_validation_status": cross_validation_status,
        "cross_validation_score": score,
        "issues": issues,
        "warnings": warnings,
    }

    path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

def write_outputs(summary: dict):
    GENERATED_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    UPDATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    stem = summary["country_file"].replace(".json", "")
    out_json = GENERATED_OUTPUTS_DIR / f"{stem}_reaudit_{date.today().isoformat()}.json"
    out_log = UPDATE_LOGS_DIR / f"{stem}_reaudit_{date.today().isoformat()}.json"

    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_log.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_json, out_log

def main() -> int:
    total = 0
    for path in sorted(COUNTRY_CARDS_DIR.glob("*.json")):
        card = load_json_loose(path)
        if card.get("policy_version") != "v0.2-deep-fetch-patch":
            continue

        summary = re_audit_country_card(path)
        out_json, out_log = write_outputs(summary)

        print(f"[OK] reaudited {path.name} => {summary['audit_status']} / {summary['cross_validation_status']}({summary['cross_validation_score']})")
        print(f"[OK] summary => {out_json.name}")
        print(f"[OK] log => {out_log.name}")
        total += 1

    print(f"[DONE] total reaudited country cards = {total}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
