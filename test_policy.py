# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from core.policy.policy_engine import check_policy

tests = [
    ("Algeria", {"model": "Toyota Prado", "year": 2021, "fuel": "gasoline", "steering": "LHD"}),
    ("Algeria", {"model": "Toyota Prado", "year": 2015, "fuel": "diesel", "steering": "LHD"}),
    ("Ghana", {"model": "Toyota Hiace", "year": 2012, "fuel": "diesel", "steering": "RHD"}),
    ("UnknownLand", {"model": "Toyota Camry", "year": 2019, "fuel": "hybrid", "steering": "LHD"})
]

for country, vehicle in tests:
    r = check_policy(country, vehicle)
    print("=" * 60)
    print("Destination:", country)
    print("Vehicle:", vehicle)
    print("Status:", r["status"])
    print("Reasons:", r["reasons"])
    print("Notes:", r["notes"])


