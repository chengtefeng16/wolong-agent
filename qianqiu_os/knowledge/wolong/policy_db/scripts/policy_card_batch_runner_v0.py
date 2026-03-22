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
import importlib.util

BASE = Path(__file__).resolve().parents[1]
COUNTRY_CARDS_DIR = BASE / "country_cards"
UPDATE_LOGS_DIR = BASE / "update_logs"

AUDIT_SCRIPT = BASE.parent / "audit" / "scripts" / "policy_authenticity_audit_v0.py"

def ensure_dirs() -> None:
    COUNTRY_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    UPDATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def schedule_dates(today: date) -> dict:
    return {
        "last_checked_at": str(today),
        "next_small_update_due": str(today + timedelta(days=3)),
        "next_major_update_due": str(today + timedelta(days=7)),
    }

def write_update_log(country_name_en: str, source_count: int, card_file: str) -> None:
    today = date.today()
    run_id = f"{country_name_en.lower().replace(' ', '_')}_{today.isoformat()}"
    log = {
        "run_id": run_id,
        "run_time": today.isoformat(),
        "target_country": country_name_en,
        "source_count": source_count,
        "new_sources_found": source_count,
        "fields_extracted": [],
        "fields_updated": [],
        "pending_verification_count": 0,
        "next_small_update_due": str(today + timedelta(days=3)),
        "next_major_update_due": str(today + timedelta(days=7)),
        "human_review_needed": True,
        "card_file": card_file
    }
    out = UPDATE_LOGS_DIR / f"{run_id}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def create_or_update_country_card(
    country_code: str,
    country_name_en: str,
    country_name_zh: str,
    region_pack: str,
    source_records: list,
    patch: dict | None = None,
) -> Path:
    ensure_dirs()
    path = COUNTRY_CARDS_DIR / f"{country_name_en.lower().replace(' ', '_')}.json"
    today = date.today()

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "country_code": country_code,
            "country_name_en": country_name_en,
            "country_name_zh": country_name_zh,
            "region_pack": region_pack,
            "status": "pending_verification",
            "policy_version": "v0.1-skeleton",
            "confidence_level": "medium",
            "last_checked_at": "",
            "next_small_update_due": "",
            "next_major_update_due": "",
            "source_records": [],
            "eligibility_scope": {},
            "access_rules": {},
            "tax_rules": {},
            "customs_and_documents": {},
            "logistics_and_delivery": {},
            "risk_and_review": {},
            "output_support": {},
            "pending_tasks": []
        }

    data.update(schedule_dates(today))
    data["source_records"] = source_records

    if patch:
        for k, v in patch.items():
            data[k] = v

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_update_log(country_name_en, len(source_records), path.name)
    return path

COUNTRY_BATCH = [
    {
        "country_code": "DZ",
        "country_name_en": "Algeria",
        "country_name_zh": "阿尔及利亚",
        "region_pack": "africa",
        "source_records": [
            {
                "source_id": "dz_official_2023_decret_23_74",
                "source_type": "official_pdf",
                "source_level": "A",
                "title": "Décret exécutif n° 23-74 du 20 février 2023",
                "language": "fr",
                "status": "structured_v1",
                "notes": "样板卡来源"
            }
        ],
        "patch": {
            "status": "restricted",
            "policy_version": "v0.2-structured-from-official-pdf",
            "confidence_level": "high"
        }
    },
    {
        "country_code": "SA",
        "country_name_en": "Saudi Arabia",
        "country_name_zh": "沙特阿拉伯",
        "region_pack": "middle_east",
        "source_records": [
            {
                "source_id": "sa_zatca_vehicle_import_controls_v1",
                "source_type": "official_web",
                "source_level": "A",
                "title": "ZATCA vehicle import controls",
                "language": "en",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "AE",
        "country_name_en": "United Arab Emirates",
        "country_name_zh": "阿联酋",
        "region_pack": "middle_east",
        "source_records": [
            {
                "source_id": "ae_moiat_customs_vehicle_import_v1",
                "source_type": "official_web",
                "source_level": "A",
                "title": "UAE vehicle import related official guidance",
                "language": "en",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "GH",
        "country_name_en": "Ghana",
        "country_name_zh": "加纳",
        "region_pack": "africa",
        "source_records": [
            {
                "source_id": "gh_customs_import_guidance_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Ghana import guidance initial source",
                "language": "en",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "MX",
        "country_name_en": "Mexico",
        "country_name_zh": "墨西哥",
        "region_pack": "latin_america",
        "source_records": [
            {
                "source_id": "mx_customs_vehicle_import_guidance_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Mexico vehicle import guidance initial source",
                "language": "es",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "AM",
        "country_name_en": "Armenia",
        "country_name_zh": "亚美尼亚",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "am_official_import_rules_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Armenia import rules initial source",
                "language": "hy",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "KZ",
        "country_name_en": "Kazakhstan",
        "country_name_zh": "哈萨克斯坦",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "kz_egov_adilet_import_rules_v1",
                "source_type": "official_web",
                "source_level": "A",
                "title": "Kazakhstan import rules initial source",
                "language": "ru",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "KG",
        "country_name_en": "Kyrgyzstan",
        "country_name_zh": "吉尔吉斯斯坦",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "kg_import_rules_initial_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Kyrgyzstan import rules initial source",
                "language": "ru",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "UZ",
        "country_name_en": "Uzbekistan",
        "country_name_zh": "乌兹别克斯坦",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "uz_import_rules_initial_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Uzbekistan import rules initial source",
                "language": "uz",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "TJ",
        "country_name_en": "Tajikistan",
        "country_name_zh": "塔吉克斯坦",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "tj_import_rules_initial_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Tajikistan import rules initial source",
                "language": "tg",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    },
    {
        "country_code": "TM",
        "country_name_en": "Turkmenistan",
        "country_name_zh": "土库曼斯坦",
        "region_pack": "central_asia",
        "source_records": [
            {
                "source_id": "tm_import_rules_initial_v1",
                "source_type": "official_or_high_trust_web",
                "source_level": "B",
                "title": "Turkmenistan import rules initial source",
                "language": "tk",
                "status": "discovered",
                "notes": "待进一步结构化"
            }
        ],
        "patch": {
            "status": "pending_verification",
            "policy_version": "v0.1-batch-init",
            "confidence_level": "medium",
            "output_support": {
                "customer_safe_explanation_template": "Initial source discovered. Further structured verification is still required before using as a final customer-facing rule."
            }
        }
    }
]

def load_audit_module():
    spec = importlib.util.spec_from_file_location("policy_authenticity_audit_v0", AUDIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def main() -> int:
    ensure_dirs()
    audit_module = load_audit_module()

    written = []
    for item in COUNTRY_BATCH:
        path = create_or_update_country_card(
            country_code=item["country_code"],
            country_name_en=item["country_name_en"],
            country_name_zh=item["country_name_zh"],
            region_pack=item["region_pack"],
            source_records=item["source_records"],
            patch=item["patch"],
        )
        summary = audit_module.audit_country_card(path)
        audit_module.write_audit_result(path, summary)
        audit_out = audit_module.write_audit_log(summary)

        print(f"[OK] wrote {path.name}")
        print(f"[OK] audit {path.name} => {summary['audit_status']} ({audit_out.name})")
        written.append(path.name)

    print(f"[DONE] batch wrote and audited {len(written)} country cards")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
