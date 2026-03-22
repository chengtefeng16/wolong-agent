# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

# qianqiu_os/agents/wolong_agent.py

class WolongAgent:
    def __init__(self, tool_registry=None, audit_logger=None):
        self.tool_registry = tool_registry
        self.audit_logger = audit_logger
        self.agent_id = "wolong"

    def can_handle(self, task_type):
        return task_type in ["policy_check", "wolong_customer_inquiry"]

    def handle_task(self, task):
        tool_result = None

        if self.tool_registry:
            tool_func = self.tool_registry.get("wolong_policy_check_tool")
            if tool_func:
                message_text = ""
                user_profile = {}
                metadata = {}

                if hasattr(task, "input_payload") and isinstance(task.input_payload, dict):
                    message_text = task.input_payload.get("message_text", "")
                    user_profile = task.input_payload.get("user_profile", {}) or {}
                    metadata = task.input_payload.get("metadata", {}) or {}

                policy_input = {
                    "destination_country": "Kenya",
                    "vehicle_year": 2018,
                    "fuel_type": "petrol",
                    "vehicle_type": "SUV",
                    "steering": "unknown",
                    "emission_standard": "unknown",
                    "message_text": message_text,
                    "user_profile": user_profile,
                    "metadata": metadata,
                }

                tool_result = tool_func(policy_input)

        if tool_result is None:
            tool_result = {
                "risk_level": "unknown",
                "policy_health": {
                    "is_outdated": False
                },
                "policy_meta": {
                    "confidence_level": 0.80
                },
                "summary": "No tool result generated."
            }

        if "policy_health" not in tool_result:
            tool_result["policy_health"] = {
                "is_outdated": False
            }

        if "policy_meta" not in tool_result:
            tool_result["policy_meta"] = {
                "confidence_level": 0.80
            }

        return {
            "agent_id": self.agent_id,
            "task_id": getattr(task, "task_id", "unknown"),
            "tool_result": tool_result,
            "status": "handled"
        }


WOLONG_AGENT_PROFILE = {
    "agent_name": "wolong_agent",
    "display_name": "卧龙 Agent",
    "agent_type": "business_service_agent",
    "description": "二手车国际贸易客户咨询与初筛样板 Agent",
    "supported_task_types": [
        "wolong_customer_inquiry",
        "policy_check"
    ],
    "default_tools": [
        "wolong_policy_check_tool"
    ],
    "channel_policy": {
        "allowed_channels": [
            "whatsapp_mock",
            "manual_input",
            "facebook"
        ]
    },
    "capability_boundary": {
        "can_do": [
            "language_detection",
            "customer_inquiry_routing",
            "preliminary_policy_check",
            "draft_reply_generation",
            "manual_review_handoff"
        ],
        "cannot_do": [
            "final_trade_commitment",
            "final_customs_commitment",
            "final_tax_commitment",
            "final_shipping_commitment"
        ]
    },
    "human_confirmation_required": True
}