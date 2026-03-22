# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# qianqiu_os/data/wolong_policy_rules.py

WOLONG_POLICY_RULES = {
    "Kenya": {
        "supported": True,
        "max_vehicle_age": 8,
        "allowed_fuel_types": ["petrol", "diesel", "hybrid"],
        "requires_manual_review": True,
        "notes": [
            "Local compliance confirmation is required."
        ]
    },
    "Tanzania": {
        "supported": True,
        "max_vehicle_age": 10,
        "allowed_fuel_types": ["petrol", "diesel", "hybrid"],
        "requires_manual_review": True,
        "notes": [
            "Final import conditions should be manually reviewed."
        ]
    },
    "Uganda": {
        "supported": True,
        "max_vehicle_age": 15,
        "allowed_fuel_types": ["petrol", "diesel", "hybrid"],
        "requires_manual_review": True,
        "notes": [
            "Preliminary result only, confirm compliance manually."
        ]
    }
}