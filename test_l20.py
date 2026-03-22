# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from compliance_core.loader import load_country_rules
from compliance_core.engine import evaluate_vehicle
from compliance_core.models import VehicleInput


# 加载阿联酋规则
rules = load_country_rules("uae")

# 构建一台测试车辆
vehicle = VehicleInput(
    model="Toyota Camry",
    year=2020,
    vehicle_type="passenger",
    fuel="petrol",
    engine_displacement=2.5,
    steering="LHD",
    emission_standard="Euro5",
    gcc_certified=False,
    accident=False,
    flood_damage=False
)

# 运行合规判断
result = evaluate_vehicle(vehicle, rules)

# 打印结果
print(result)

