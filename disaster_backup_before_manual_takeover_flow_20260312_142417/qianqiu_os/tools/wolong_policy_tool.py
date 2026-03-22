# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# qianqiu_os/tools/wolong_policy_tool.py

from datetime import datetime

from qianqiu_os.data.wolong_policy_rules import WOLONG_POLICY_RULES


def wolong_policy_check_tool(policy_input: dict) -> dict:
    destination_country = str(policy_input.get("destination_country", "unknown")).strip()
    vehicle_year = policy_input.get("vehicle_year")
    fuel_type = str(policy_input.get("fuel_type", "unknown")).strip().lower()
    vehicle_type = str(policy_input.get("vehicle_type", "unknown")).strip()
    steering = str(policy_input.get("steering", "unknown")).strip().lower()
    emission_standard = str(policy_input.get("emission_standard", "unknown")).strip()

    current_year = datetime.now().year
    missing_fields = []
    rule_hits = []
    notes = []

    if steering in ["", "unknown", "none"]:
        missing_fields.append("steering")

    if emission_standard in ["", "unknown", "none"]:
        missing_fields.append("emission_standard")

    country_rules = WOLONG_POLICY_RULES.get(destination_country)

    if not country_rules:
        return {
            "tool_name": "wolong_policy_check_tool",
            "executed": True,
            "allowed": False,
            "risk_level": "high",
            "manual_review_required": True,
            "rule_hits": [],
            "policy_summary": f"No policy sample rules found for {destination_country}. Manual review is required.",
            "missing_fields": missing_fields,
            "notes": [
                "Destination country is not yet included in the current policy sample set.",
                "This is only a preliminary screening result."
            ],
            "vehicle_type": vehicle_type,
            "destination_country": destination_country,
        }

    rule_hits.append("country_supported")

    supported = bool(country_rules.get("supported", False))
    max_vehicle_age = int(country_rules.get("max_vehicle_age", 0))
    allowed_fuel_types = country_rules.get("allowed_fuel_types", [])
    requires_manual_review = bool(country_rules.get("requires_manual_review", True))
    country_notes = country_rules.get("notes", [])

    if not supported:
        return {
            "tool_name": "wolong_policy_check_tool",
            "executed": True,
            "allowed": False,
            "risk_level": "high",
            "manual_review_required": True,
            "rule_hits": rule_hits,
            "policy_summary": f"Preliminary rules indicate {destination_country} is not currently supported in this sample policy tool.",
            "missing_fields": missing_fields,
            "notes": country_notes,
            "vehicle_type": vehicle_type,
            "destination_country": destination_country,
        }

    vehicle_age = None
    if isinstance(vehicle_year, int):
        vehicle_age = current_year - vehicle_year
    else:
        missing_fields.append("vehicle_year")

    allowed = True
    risk_level = "medium"

    if vehicle_age is not None:
        if vehicle_age <= max_vehicle_age:
            rule_hits.append("vehicle_age_check_passed")
        else:
            rule_hits.append("vehicle_age_check_failed")
            allowed = False
            risk_level = "high"
            notes.append(
                f"Vehicle age appears to exceed the sample threshold of {max_vehicle_age} years."
            )

    if fuel_type in allowed_fuel_types:
        rule_hits.append("fuel_type_check_passed")
    else:
        if fuel_type in ["", "unknown", "none"]:
            missing_fields.append("fuel_type")
            notes.append("Fuel type is missing or unclear.")
        else:
            rule_hits.append("fuel_type_check_failed")
            allowed = False
            risk_level = "high"
            notes.append(
                f"Fuel type '{fuel_type}' is not listed in the current sample allowed fuel types."
            )

    notes.extend(country_notes)

    if allowed:
        policy_summary = (
            f"Preliminary policy review suggests the {vehicle_year} {fuel_type} {vehicle_type} "
            f"may be eligible for import into {destination_country}, but manual confirmation is still required."
        )
    else:
        policy_summary = (
            f"Preliminary policy review suggests this vehicle may not meet the current sample rules "
            f"for import into {destination_country}. Manual review is required."
        )

    return {
        "tool_name": "wolong_policy_check_tool",
        "executed": True,
        "allowed": allowed,
        "risk_level": risk_level,
        "manual_review_required": requires_manual_review or (len(missing_fields) > 0),
        "rule_hits": rule_hits,
        "policy_summary": policy_summary,
        "missing_fields": missing_fields,
        "notes": notes,
        "vehicle_type": vehicle_type,
        "destination_country": destination_country,
        "vehicle_year": vehicle_year,
        "fuel_type": fuel_type,
        "steering": steering,
        "emission_standard": emission_standard,
    }