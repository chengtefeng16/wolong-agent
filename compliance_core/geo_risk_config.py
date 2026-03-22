# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# compliance_core/geo_risk_config.py

CURRENT_GEO_POLITICAL_RISK = {
    "level": "warning",  
    # none / warning / elevated / confirmed

    "region": "Middle East",
    "affected_route": "Strait of Hormuz",

    "business_effect": "possible shipping delay",

    "key_assumptions": [
        "Shipping lane remains open",
        "Marine insurance available",
        "No formal trade ban",
        "Port operations functioning normally",
        "International banking settlement operational"
    ],

    "last_updated": "2026-03-01"
}

