# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from qianqiu_os.data.wolong_policy_rules import WOLONG_POLICY_RULES


def _normalize_country(country_code_or_name):
    text = str(country_code_or_name or "").strip().lower()

    mapping = {
        "ke": "Kenya",
        "kenya": "Kenya",
        "ug": "Uganda",
        "uganda": "Uganda",
        "tz": "Tanzania",
        "tanzania": "Tanzania",
        "rw": "Rwanda",
        "rwanda": "Rwanda",
        "zm": "Zambia",
        "zambia": "Zambia",
        "gh": "Ghana",
        "ghana": "Ghana",
        "ng": "Nigeria",
        "nigeria": "Nigeria",
    }
    return mapping.get(text, country_code_or_name or "Unknown")


def _get_country_rule(country_name):
    if not isinstance(WOLONG_POLICY_RULES, dict):
        return {}

    for key, value in WOLONG_POLICY_RULES.items():
        if str(key).strip().lower() == str(country_name).strip().lower():
            return value if isinstance(value, dict) else {}

    return {}


def _build_missing_fields(vehicle):
    missing = []

    steering = str(vehicle.get("steering", "") or "").lower()
    emission = str(vehicle.get("emission", "") or "").lower()

    if not steering or steering == "unknown":
        missing.append("steering")

    if not emission or emission == "unknown":
        missing.append("emission_standard")

    return missing


def policy_check_tool(input_payload):
    input_payload = input_payload or {}
    vehicle = input_payload.get("vehicle", {}) or {}

    country_name = _normalize_country(input_payload.get("country_code_or_name"))
    rule = _get_country_rule(country_name)

    vehicle_age = vehicle.get("age")
    fuel_type = vehicle.get("fuel", "unknown")
    steering = vehicle.get("steering", "unknown")
    emission_standard = vehicle.get("emission", "unknown")
    certification = vehicle.get("certification", False)
    vehicle_year = input_payload.get("vehicle_year")
    vehicle_type = vehicle.get("type", "vehicle")

    max_age = rule.get("max_vehicle_age")
    allowed_fuels = rule.get("allowed_fuels", [])

    rule_hits = []
    notes = []
    missing_fields = _build_missing_fields(vehicle)

    allowed = True
    manual_review_required = True
    risk_level = "medium"

    if rule:
        rule_hits.append("country_supported")
    else:
        notes.append("Destination country rule is not fully configured. Manual review required.")

    if isinstance(vehicle_age, int) and isinstance(max_age, int):
        if vehicle_age <= max_age:
            rule_hits.append("vehicle_age_check_passed")
        else:
            allowed = False
            risk_level = "high"
            notes.append(f"Vehicle age {vehicle_age} exceeds allowed max age {max_age}.")
    else:
        notes.append("Vehicle age rule could not be fully verified.")

    if allowed_fuels:
        if fuel_type in allowed_fuels:
            rule_hits.append("fuel_type_check_passed")
        else:
            allowed = False
            risk_level = "high"
            notes.append(f"Fuel type {fuel_type} is not in allowed list: {allowed_fuels}.")
    else:
        notes.append("Fuel type rule could not be fully verified.")

    if certification:
        rule_hits.append("certification_present")
    else:
        notes.append("Certification status requires manual confirmation.")

    if missing_fields:
        notes.append("Some compliance fields are missing and require manual confirmation.")

    if not notes:
        notes.append("Local compliance confirmation is required.")

    policy_summary = (
        f"Preliminary policy review for {country_name}: "
        f"vehicle may {'be eligible' if allowed else 'not be eligible'} for import, "
        f"but manual confirmation is still required."
    )

    return {
        "tool_name": "wolong_policy_check_tool",
        "executed": True,
        "allowed": allowed,
        "risk_level": risk_level,
        "manual_review_required": manual_review_required,
        "rule_hits": rule_hits,
        "policy_summary": policy_summary,
        "missing_fields": missing_fields,
        "notes": notes,
        "vehicle_type": vehicle_type,
        "destination_country": country_name,
        "vehicle_year": vehicle_year,
        "fuel_type": fuel_type,
        "steering": steering,
        "emission_standard": emission_standard,
        "policy_health": {
            "is_outdated": False
        },
        "policy_meta": {
            "confidence_level": 0.8
        },
        "status": "handled"
    }
