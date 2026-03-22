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
COUNTRY_CARDS = BASE / "policy_db" / "country_cards"
GENERATED_OUTPUTS = BASE / "policy_db" / "generated_outputs"

OFFICIAL_TYPES = {"official_pdf", "official_web", "official_gazette", "official_law_db"}
HIGH_TRUST_TYPES = {"official_or_high_trust_web", "industry_high_trust", "embassy_or_trade_service"}
SOFT_SIGNAL_TYPES = {"forum", "community", "operational_feedback", "market_rumor"}

def parse_date_safe(value: str):
    try:
        return date.fromisoformat(value)
    except Exception:
        return None

def normalize_source_coverage(source_records: list) -> dict:
    """
    从 notes/title/source_type 中做非常轻量的渠道覆盖判断。
    当前是 V0.1：先保守，不做复杂 NLP。
    """
    coverage = {
        "customs": False,
        "tax_or_revenue": False,
        "transport_or_industry_or_trade": False,
        "official_gazette_or_law_db": False,
        "high_trust_industry_or_embassy": False,
        "soft_signals_only": False,
    }

    if not source_records:
        coverage["soft_signals_only"] = False
        return coverage

    all_soft = True
    for rec in source_records:
        text = " ".join([
            str(rec.get("source_type", "")),
            str(rec.get("title", "")),
            str(rec.get("notes", "")),
            str(rec.get("source_id", "")),
        ]).lower()

        stype = str(rec.get("source_type", "")).lower()

        if stype not in SOFT_SIGNAL_TYPES:
            all_soft = False

        if "custom" in text or "douane" in text or "aduana" in text or "zatca" in text:
            coverage["customs"] = True
        if "tax" in text or "revenue" in text or "vat" in text or "fiscal" in text:
            coverage["tax_or_revenue"] = True
        if "transport" in text or "industry" in text or "trade" in text or "moiat" in text or "econom" in text:
            coverage["transport_or_industry_or_trade"] = True
        if "gazette" in text or "law" in text or "decret" in text or "journal officiel" in text:
            coverage["official_gazette_or_law_db"] = True
        if stype in HIGH_TRUST_TYPES or "commercial service" in text or "embassy" in text:
            coverage["high_trust_industry_or_embassy"] = True

    coverage["soft_signals_only"] = all_soft
    return coverage

def cross_validation_score(source_records: list, coverage: dict) -> int:
    """
    V0.1 的交叉验证粗分：
    - 多条来源 + 多种渠道覆盖 -> 分更高
    - 单一来源或单一渠道 -> 分更低
    """
    score = 0
    if len(source_records) >= 1:
        score += 1
    if len(source_records) >= 2:
        score += 1

    for key in ["customs", "tax_or_revenue", "transport_or_industry_or_trade", "official_gazette_or_law_db", "high_trust_industry_or_embassy"]:
        if coverage.get(key):
            score += 1
    return score

def classify_cross_validation_status(score: int) -> str:
    if score >= 5:
        return "strong"
    if score >= 3:
        return "medium"
    return "weak"

def audit_country_card(path: Path) -> dict:
    card = json.loads(path.read_text(encoding="utf-8"))
    today = date.today()

    issues = []
    warnings = []

    source_records = card.get("source_records", []) or []
    confidence_level = card.get("confidence_level", "")
    last_checked_at = parse_date_safe(card.get("last_checked_at", ""))
    next_small = parse_date_safe(card.get("next_small_update_due", ""))
    next_major = parse_date_safe(card.get("next_major_update_due", ""))
    status = str(card.get("status", ""))
    policy_version = str(card.get("policy_version", ""))
    rr = card.get("risk_and_review", {}) or {}
    manual_review_required_cases = rr.get("manual_review_required_cases", []) or []
    enforcement_uncertainty_notes = rr.get("enforcement_uncertainty_notes", []) or []
    output_support = card.get("output_support", {}) or {}
    customer_safe_explanation_template = output_support.get("customer_safe_explanation_template", "")

    if not source_records:
        issues.append("missing_source_records")

    if not confidence_level:
        issues.append("missing_confidence_level")

    if not last_checked_at:
        issues.append("missing_last_checked_at")

    if not next_small:
        issues.append("missing_next_small_update_due")
    elif next_small < today:
        issues.append("next_small_update_due_expired")

    if not next_major:
        issues.append("missing_next_major_update_due")
    elif next_major < today:
        issues.append("next_major_update_due_expired")

    if not customer_safe_explanation_template:
        issues.append("missing_customer_safe_explanation_template")

    # 新增：来源广度与交叉验证检查
    coverage = normalize_source_coverage(source_records)
    score = cross_validation_score(source_records, coverage)
    cross_validation_status = classify_cross_validation_status(score)

    if coverage["soft_signals_only"]:
        issues.append("soft_signals_only_not_allowed_for_formal_pass")

    if cross_validation_status == "weak":
        warnings.append("cross_validation_weak")

    # 新增：初始发现态 / 批量建壳态默认不能 pass
    if status == "pending_verification":
        warnings.append("status_pending_verification")

    if policy_version == "v0.1-batch-init":
        warnings.append("policy_version_batch_init")

    if manual_review_required_cases:
        warnings.append("manual_review_required_cases_present")

    if enforcement_uncertainty_notes:
        warnings.append("enforcement_uncertainty_notes_present")

    # 判定收紧逻辑
    if "missing_source_records" in issues or "missing_last_checked_at" in issues:
        audit_status = "audit_fail"
    elif "soft_signals_only_not_allowed_for_formal_pass" in issues:
        audit_status = "audit_fail"
    elif status == "pending_verification":
        audit_status = "audit_restricted"
    elif policy_version == "v0.1-batch-init":
        audit_status = "audit_restricted"
    elif manual_review_required_cases or enforcement_uncertainty_notes:
        audit_status = "audit_restricted"
    elif cross_validation_status == "weak":
        audit_status = "audit_pass_with_warning"
    elif issues:
        audit_status = "audit_restricted"
    elif warnings:
        audit_status = "audit_pass_with_warning"
    else:
        audit_status = "audit_pass"

    summary = {
        "country_name_en": card.get("country_name_en"),
        "audit_status": audit_status,
        "issues": issues,
        "warnings": warnings,
        "checked_at": str(today),
        "human_review_needed": audit_status in {"audit_restricted", "audit_fail"},
        "source_coverage": coverage,
        "cross_validation_score": score,
        "cross_validation_status": cross_validation_status,
    }
    return summary

def write_audit_result(card_path: Path, summary: dict) -> None:
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card["audit_status"] = summary["audit_status"]
    card["audit_summary"] = {
        "issues": summary["issues"],
        "warnings": summary["warnings"],
        "human_review_needed": summary["human_review_needed"],
        "source_coverage": summary["source_coverage"],
        "cross_validation_score": summary["cross_validation_score"],
        "cross_validation_status": summary["cross_validation_status"],
    }
    card["audit_last_checked_at"] = summary["checked_at"]
    card["source_validation_summary"] = {
        "source_coverage": summary["source_coverage"],
        "cross_validation_score": summary["cross_validation_score"],
        "cross_validation_status": summary["cross_validation_status"],
    }
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_audit_log(summary: dict) -> Path:
    GENERATED_OUTPUTS.mkdir(parents=True, exist_ok=True)
    out = GENERATED_OUTPUTS / f"{summary['country_name_en'].lower().replace(' ', '_')}_audit_{summary['checked_at']}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out

def main() -> int:
    card_path = COUNTRY_CARDS / "algeria.json"
    if not card_path.exists():
        raise SystemExit(f"[ERROR] missing country card: {card_path}")

    summary = audit_country_card(card_path)
    write_audit_result(card_path, summary)
    out = write_audit_log(summary)

    print(f"[OK] audit_status={summary['audit_status']}")
    print(f"[OK] cross_validation_status={summary['cross_validation_status']}")
    print(f"[OK] wrote audit log: {out.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
