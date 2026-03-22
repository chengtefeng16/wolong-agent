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

BASE = Path(__file__).resolve().parents[2]
COUNTRY_CARD = BASE / "country_cards" / "algeria.json"
GENERATED_OUTPUTS = BASE / "generated_outputs"
PENDING_VERIFICATION = BASE / "pending_verification"
UPDATE_LOGS = BASE / "update_logs"

def ensure_dirs() -> None:
    GENERATED_OUTPUTS.mkdir(parents=True, exist_ok=True)
    PENDING_VERIFICATION.mkdir(parents=True, exist_ok=True)
    UPDATE_LOGS.mkdir(parents=True, exist_ok=True)

def build_algeria_patch() -> dict:
    """
    Algeria 样板抽取脚本 V0
    当前阶段先将已确认法规事实写成结构化 patch。
    后续可升级为：
    - 从 PDF/网页句段抽取
    - 字段置信度打分
    - uncertain 字段自动流入 pending_verification
    """
    return {
        "status": "restricted",
        "policy_version": "v0.3-extractor-patch",
        "confidence_level": "high",
        "eligibility_scope": {
            "applicable_person_type": "resident_individual_only",
            "usage_scope": "personal_use_only",
            "frequency_limit": "one_import_every_3_years"
        },
        "access_rules": {
            "used_vehicle_import_allowed": True,
            "allowed_vehicle_types": [
                "tourism_vehicle_electric",
                "tourism_vehicle_petrol",
                "tourism_vehicle_hybrid",
                "light_utility_vehicle_electric",
                "light_utility_vehicle_petrol",
                "light_utility_vehicle_hybrid",
                "van",
                "small_van",
                "pickup_under_3_5_tons"
            ],
            "max_vehicle_age_years": 3,
            "steering_requirement": "pending_verification_in_source",
            "fuel_type_rules": [
                "electric",
                "petrol",
                "hybrid_petrol_electric"
            ],
            "emission_rules": [
                "must_meet_regulatory_safety_and_environmental_requirements"
            ],
            "certification_rules": [
                "conformity_expertise_report_required"
            ],
            "special_restrictions": [
                "resident_individual_only",
                "personal_use_only",
                "temporary_tourist_entry_excluded"
            ]
        },
        "tax_rules": {
            "tariff_rule": "duties_and_taxes_payable_under_applicable_legislation",
            "vat_rule": "pending_verification_in_source",
            "additional_tax_rule": "pending_verification_in_source",
            "fee_notes": [
                "clearance for release into consumption is subject to payment of duties and taxes due"
            ],
            "currency_notes": [
                "used vehicle imports by resident individuals are made using their own foreign currency"
            ]
        },
        "customs_and_documents": {
            "required_documents": [
                "copy_of_identity_document_or_resident_card",
                "residence_certificate",
                "foreign_vehicle_registration_or_equivalent",
                "proof_of_transfer_of_ownership_invoice_and_or_sale_contract",
                "document_less_than_3_months_old_proving_vehicle_good_working_condition",
                "conformity_expertise_report_from_approved_expert"
            ],
            "customs_clearance_requirements": [
                "clearance_file_submitted_at_entry_or_competent_customs_office",
                "temporary_customs_passage_title_valid_for_one_month_non_extendable_before_release"
            ],
            "inspection_requirements": [
                "vehicle_must_be_in_good_working_condition",
                "vehicle_must_not_have_major_or_critical_defects"
            ],
            "compliance_report_requirements": [
                "approved_mines_ministry_expert_conformity_report"
            ],
            "foreign_exchange_requirements": [
                "resident_individual_uses_own_foreign_currency"
            ]
        },
        "logistics_and_delivery": {
            "common_ports_or_border_points": [],
            "logistics_constraints": [
                "temporary_admission_title_valid_for_one_month_and_not_extendable"
            ],
            "transport_risk_notes": [
                "late_or_incomplete_customs_file_may_delay_release_into_consumption"
            ]
        },
        "risk_and_review": {
            "risk_flags": [
                "resident_individual_scope_only",
                "personal_use_only",
                "three_year_vehicle_age_limit",
                "one_import_every_three_years",
                "own_foreign_currency_requirement",
                "non_conformity_may_trigger_reexport"
            ],
            "manual_review_required_cases": [
                "vehicle_type_classification_unclear",
                "fuel_type_not_explicitly_listed",
                "tax_breakdown_needed_for_customer_quote",
                "diplomatic_or_consular_transfer_case",
                "steering_requirement_not_explicit_in_current_source"
            ],
            "enforcement_uncertainty_notes": [
                "exact_tax_component_breakdown_not_specified_in_current_uploaded_source",
                "steering_side_requirement_not_explicitly_stated_in_current_uploaded_source"
            ],
            "operational_warnings": [
                "do_not_treat_as_dealer_import_rule",
                "do_not_extrapolate_beyond_resident_individual_personal_use_scope_without_additional_source_validation"
            ]
        },
        "output_support": {
            "internal_summary_template": "Algeria currently allows certain used passenger and light utility vehicles for resident individuals only, for personal use, with a 3-year age limit and once-every-3-years frequency limit; duties/taxes apply and own foreign currency is required.",
            "customer_safe_explanation_template": "For Algeria, the current rule in this source is limited to resident individuals importing eligible used vehicles for personal use, subject to age limits, required documents, applicable duties and taxes, and conformity checks.",
            "high_risk_warning_template": "Please note that this rule source is not a blanket dealer-import approval. Cases outside resident individual personal-use scope should be manually reviewed."
        }
    }

def merge_patch(card: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(card.get(key), dict):
            card[key].update(value)
        else:
            card[key] = value
    return card

def write_pending_verification_snapshot(card: dict) -> Path:
    snapshot = {
        "country": "Algeria",
        "date": str(date.today()),
        "pending_verification": {
            "access_rules.steering_requirement": "pending_verification_in_source",
            "tax_rules.vat_rule": "pending_verification_in_source",
            "tax_rules.additional_tax_rule": "pending_verification_in_source"
        },
        "notes": [
            "需要补充更细税费拆分来源",
            "需要补充方向盘要求官方来源",
            "需要补充商业进口/经销商场景官方来源"
        ]
    }
    out = PENDING_VERIFICATION / f"algeria_pending_{date.today().isoformat()}.json"
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out

def write_patch_output(patch: dict) -> Path:
    out = GENERATED_OUTPUTS / f"algeria_patch_{date.today().isoformat()}.json"
    out.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out

def write_update_log() -> Path:
    today = date.today()
    log = {
        "run_id": f"algeria_extractor_v0_{today.isoformat()}",
        "run_time": today.isoformat(),
        "target_country": "Algeria",
        "source_count": 1,
        "new_sources_found": 0,
        "fields_extracted": [
            "eligibility_scope",
            "access_rules",
            "tax_rules",
            "customs_and_documents",
            "logistics_and_delivery",
            "risk_and_review",
            "output_support"
        ],
        "fields_updated": [
            "status",
            "policy_version",
            "confidence_level",
            "eligibility_scope",
            "access_rules",
            "tax_rules",
            "customs_and_documents",
            "logistics_and_delivery",
            "risk_and_review",
            "output_support"
        ],
        "pending_verification_count": 3,
        "next_small_update_due": str(today + timedelta(days=3)),
        "next_major_update_due": str(today + timedelta(days=7)),
        "human_review_needed": True,
        "pipeline_stage": "extractor_v0"
    }
    out = UPDATE_LOGS / f"algeria_extractor_v0_{today.isoformat()}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out

def main() -> int:
    ensure_dirs()
    if not COUNTRY_CARD.exists():
        raise SystemExit(f"[ERROR] missing country card: {COUNTRY_CARD}")

    card = json.loads(COUNTRY_CARD.read_text(encoding="utf-8"))
    patch = build_algeria_patch()

    card = merge_patch(card, patch)
    card["last_checked_at"] = str(date.today())
    card["next_small_update_due"] = str(date.today() + timedelta(days=3))
    card["next_major_update_due"] = str(date.today() + timedelta(days=7))
    card["policy_version"] = "v0.3-extractor-patch"

    COUNTRY_CARD.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    patch_out = write_patch_output(patch)
    pending_out = write_pending_verification_snapshot(card)
    log_out = write_update_log()

    print(f"[OK] updated {COUNTRY_CARD.name}")
    print(f"[OK] wrote patch output: {patch_out.name}")
    print(f"[OK] wrote pending verification: {pending_out.name}")
    print(f"[OK] wrote extractor log: {log_out.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
