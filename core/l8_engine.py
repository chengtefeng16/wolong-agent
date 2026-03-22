# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from core.export_factors import export_context
from core.policy.policy_engine import check_policy
from core.policy.policy_monitor import check_policy_update_status


def build_sample_output(destination, vehicle_list, identity="individual"):
    """
    vehicle_list: list of vehicle dicts
    identity: individual / dealer
    """

    units = sum(v.get("units", 1) for v in vehicle_list)

    # 调用政策引擎（L9）
    policy_result = check_policy(destination, vehicle_list[0])

    # 调用更新检测（L9.3）
    policy_update_status = check_policy_update_status(destination)

    # 如果政策需要更新，追加 warning
    if policy_update_status["status"] != "up_to_date":
        policy_result["warnings"] = policy_result.get("warnings", [])
        policy_result["warnings"].append(
            f"Policy update required: {policy_update_status['status']} "
            f"({policy_update_status['days_since_last_check']} days since last check)."
        )

    # 调用物流与成本结构（L8）
    export_ctx = export_context(destination, vehicle_list[0], units=units)

    output = {
        "meta": {
            "destination": destination,
            "identity": identity,
            "total_units": units
        },
        "vehicle_samples": vehicle_list,
        "policy_check": policy_result,
        "logistics_preview": {
            "domestic": export_ctx["domestic_logistics"],
            "international": export_ctx["international_logistics"],
            "customs": export_ctx["customs_export_fees"]
        },
        "cost_preview": {
            "vehicle_cost": None,
            "estimated_total": None,
            "currency": "USD"
        }
    }

    # 自然话术生成（简单版）
    if identity == "dealer":
        output["natural_reply"] = (
            "Below are several available units matching your market needs. "
            "Please review the specifications and let me know which models you would like to proceed with."
        )
    else:
        output["natural_reply"] = (
            "Here are some suitable options for your reference. "
            "Please let me know which vehicle you are most interested in."
        )

    return output

