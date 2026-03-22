# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from datetime import datetime
from pathlib import Path
import json

POLICY_DIR = Path("knowledge/policies/countries")


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def check_policy_update_status(country_code: str):
    file_path = POLICY_DIR / f"{country_code.lower()}.json"

    if not file_path.exists():
        return {"status": "missing", "message": "Policy file not found."}

    policy = json.loads(file_path.read_text(encoding="utf-8"))
    meta = policy.get("meta", {})

    today = datetime.now()

    last_verified = parse_date(meta.get("last_verified_at", "2000-01-01"))
    small_cycle = meta.get("small_update_cycle_days", 3)
    major_cycle = meta.get("major_update_cycle_days", 7)

    days_since_verify = (today - last_verified).days

    if days_since_verify >= major_cycle:
        return {
            "status": "major_update_due",
            "days_since_last_check": days_since_verify
        }

    if days_since_verify >= small_cycle:
        return {
            "status": "small_update_due",
            "days_since_last_check": days_since_verify
        }

    return {
        "status": "up_to_date",
        "days_since_last_check": days_since_verify
    }

