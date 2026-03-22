# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from geo_risk_config import get_geo_political_risk


def evaluate_vehicle(vehicle, rules):

    triggered_rules = []

    # 如果是 Pydantic 模型，转成 dict
    if hasattr(rules, "model_dump"):
        rules_dict = rules.model_dump()
    else:
        rules_dict = rules

    # 年限规则
    max_age = rules_dict.get("max_vehicle_age")
    if max_age is not None:
        vehicle_age = 2026 - vehicle.year
        if vehicle_age > max_age:
            triggered_rules.append(f"Vehicle age exceeds limit ({max_age} years)")

    # 燃油规则
    allowed_fuel = rules_dict.get("allowed_fuel_types", [])
    if vehicle.fuel not in allowed_fuel:
        triggered_rules.append("Fuel type not allowed")

    # GCC认证
    if rules_dict.get("gcc_required", False):
        if not vehicle.gcc_certified:
            triggered_rules.append("GCC certification required")

    # 排放标准
    required_emission = rules_dict.get("required_emission_standard")
    if required_emission:
        if vehicle.emission_standard != required_emission:
            triggered_rules.append("Emission standard must meet GCC")

    # 判断状态
    status = "approved"
    if triggered_rules:
        status = "blocked"

    official_result = {
        "status": status,
        "triggered_rules": triggered_rules
    }

    # 三层地缘结构
    geo_environment = get_geo_political_risk()

    return {
        "official_result": official_result,
        "geo_environment": geo_environment,
        "cost_estimation": None,
        "risk_analysis": None
    }

