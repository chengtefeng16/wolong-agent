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
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any

BASE = Path(__file__).resolve().parents[1]
COUNTRY_CARDS_DIR = BASE / "country_cards"
UPDATE_LOGS_DIR = BASE / "update_logs"

@dataclass
class SourceRecord:
    source_id: str
    source_type: str
    source_level: str
    title: str
    language: str
    status: str
    notes: str = ""

def ensure_dirs() -> None:
    COUNTRY_CARDS_DIR.mkdir(parents=True, exist_ok=True)
    UPDATE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def schedule_dates(today: date) -> Dict[str, str]:
    return {
        "last_checked_at": str(today),
        "next_small_update_due": str(today + timedelta(days=3)),
        "next_major_update_due": str(today + timedelta(days=7)),
    }

def create_or_update_country_card(
    country_code: str,
    country_name_en: str,
    country_name_zh: str,
    region_pack: str,
    source_records: List[SourceRecord],
    patch: Dict[str, Any] | None = None,
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
    data["source_records"] = [asdict(s) for s in source_records]

    if patch:
        for k, v in patch.items():
            data[k] = v

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_update_log(country_name_en, len(source_records), path.name)
    return path

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
        "card_file": card_file,
    }
    out = UPDATE_LOGS_DIR / f"{run_id}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def demo_algeria() -> None:
    source = SourceRecord(
        source_id="dz_official_2023_decret_23_74",
        source_type="official_pdf",
        source_level="A",
        title="Décret exécutif n° 23-74 du 20 février 2023",
        language="fr",
        status="structured_v1",
        notes="样板卡来源"
    )
    patch = {
        "status": "restricted",
        "policy_version": "v0.2-structured-from-official-pdf",
        "confidence_level": "high"
    }
    path = create_or_update_country_card(
        country_code="DZ",
        country_name_en="Algeria",
        country_name_zh="阿尔及利亚",
        region_pack="africa",
        source_records=[source],
        patch=patch,
    )
    print(f"[OK] wrote {path}")

if __name__ == "__main__":
    demo_algeria()
