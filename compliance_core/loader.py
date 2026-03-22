# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import json
from pathlib import Path
from compliance_core.models import OfficialRules


def load_country_rules(country_code: str) -> OfficialRules:
    base_path = Path(__file__).parent
    policy_path = base_path / "policies" / f"{country_code}.json"

    if not policy_path.exists():
        raise FileNotFoundError(f"No policy file found for country: {country_code}")

    with open(policy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 直接加载企业级结构
    return OfficialRules(**data)

