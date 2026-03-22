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
import sys
import unittest
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.business_context_manager import BusinessContextManager
from qianqiu_os.services.output_adapter import OutputAdapter
from qianqiu_os.services.knowledge_access_layer import KnowledgeAccessLayer
from qianqiu_os.services.h5_delegation_config_service_v2 import H5DelegationConfigServiceV2
from qianqiu_os.services.h5_delegation_active_config_preview_v1 import build_preview
from qianqiu_os.services.h5_delegation_config_rollback_v1 import H5DelegationConfigRollbackV1
from qianqiu_os.api.h5_delegation_routes_v1 import (
    api_save_delegation_config,
    api_get_active_delegation_preview,
    api_list_delegation_snapshots,
)


class TestMainlineRegressionV1(unittest.TestCase):
    def test_business_context_manager(self):
        manager = BusinessContextManager()
        ctx = manager.build_context(
            input_context={
                "metadata": {"intent_type": "import_consulting"},
                "user_profile": {"customer_type": "dealer"},
            },
            tool_result={"risk_level": "medium"},
            wolong_result={
                "business_action_result": {
                    "business_stage": "negotiating",
                    "emotion_state": "calm",
                }
            },
            user_memory_context={"destination_country": "Kenya"},
        )

        self.assertEqual(ctx["business_stage"], "negotiating")
        self.assertEqual(ctx["risk_level"], "medium")
        self.assertEqual(ctx["destination_country"], "Kenya")
        self.assertEqual(ctx["customer_type"], "dealer")
        self.assertEqual(ctx["intent_type"], "import_consulting")
        self.assertEqual(ctx["emotion_state"], "calm")

    def test_output_adapter_runtime_policy_injection(self):
        adapter = OutputAdapter()

        result = {
            "platform_governance": {
                "manual_review_required": False,
                "governance_notes": []
            },
            "experience_reference": {
                "matched_count": 0,
                "latest_decision": None,
                "latest_note": None
            },
            "user_memory_context": {
                "customer_type": "dealer",
                "destination_country": "Kenya"
            },
            "input_context": {
                "source": "whatsapp_mock",
                "message_text": "Test runtime delegation injection",
                "metadata": {
                    "channel": "whatsapp",
                    "session_id": "wa_session_001",
                    "intent_type": "import_consulting"
                },
                "user_profile": {
                    "user_id": "wa_user_001",
                    "customer_id": "cust_001",
                    "source": "whatsapp",
                    "display_name": "test_customer",
                    "language": "en",
                    "preference": "import feasibility"
                }
            },
            "tool_result": {
                "status": "ok",
                "policy_summary": "Test summary",
                "manual_review_required": False,
                "warnings": [],
                "missing_fields": [],
                "risk_level": "medium"
            },
            "wolong_result": {
                "customer_reply_result": {
                    "reply_text": "This is a test reply."
                },
                "manual_review_result": {
                    "manual_review_required": False
                },
                "business_action_result": {
                    "business_stage": "negotiating",
                    "emotion_state": "calm"
                },
                "delegation_policy_result": {}
            }
        }

        formatted_output = adapter.format_output(
            source="whatsapp_mock",
            result=result,
        )
        policy = formatted_output.get("delegation_policy", {}) or {}
        business_context = formatted_output.get("business_context", {}) or {}

        self.assertTrue(policy.get("delegation_master_switch"))
        self.assertTrue(policy.get("delegation_enabled"))
        self.assertEqual(policy.get("delegation_stage"), "L3_small_autonomy")
        self.assertEqual(policy.get("permission_level"), "L3")
        self.assertEqual(policy.get("business_stage"), "negotiating")
        self.assertEqual(policy.get("risk_level"), "medium")
        self.assertEqual(policy.get("destination_country"), "Kenya")
        self.assertEqual(policy.get("customer_type"), "dealer")
        self.assertEqual(policy.get("intent_type"), "import_consulting")
        self.assertEqual(policy.get("emotion_state"), "calm")
        self.assertEqual(business_context.get("business_stage"), "negotiating")

    def test_knowledge_access_layer(self):
        layer = KnowledgeAccessLayer()
        self.assertTrue(layer.load_runtime_delegation_config()["success"])
        self.assertTrue(layer.load_h5_schema()["success"])
        self.assertTrue(layer.load_h5_default_config()["success"])
        self.assertTrue(layer.load_h5_presets()["success"])
        self.assertTrue(layer.load_integration_checklist()["success"])
        self.assertTrue(layer.load_wolong_faq_pack()["success"])
        self.assertTrue(layer.load_wolong_rule_pack()["success"])

    def test_save_and_preview_minimum_chain(self):
        service = H5DelegationConfigServiceV2()
        payload = {
            "operator_id": "regression_test_operator",
            "operator_name": "regression_test_operator",
            "change_reason": "regression_test_save",
            "config_version": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "applied_preset": "L3_small_autonomy_safe"
        }
        result = service.save_config(payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["applied_preset"], "L3_small_autonomy_safe")

        active_path = PROJECT_ROOT / "qianqiu_os" / "runtime_governance" / "delegation_active_config.json"
        self.assertTrue(active_path.exists())

        with open(active_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        preview = build_preview(data)
        self.assertEqual(preview["applied_preset"], "L3_small_autonomy_safe")
        self.assertTrue(preview["delegation_master_switch"])
        self.assertTrue(preview["delegation_enabled"])
        self.assertEqual(preview["delegation_stage"], "L3_small_autonomy")
        self.assertEqual(preview["permission_level"], "L3")

    def test_rollback_minimum_chain(self):
        service = H5DelegationConfigServiceV2()

        payload_old = {
            "operator_id": "rollback_test_operator_old",
            "operator_name": "rollback_test_operator_old",
            "change_reason": "rollback_test_old_save",
            "config_version": "rollback_test_old",
            "applied_preset": "L3_small_autonomy_safe"
        }
        result_old = service.save_config(payload_old)
        self.assertTrue(result_old["success"])

        snapshot_path = result_old.get("rollback_snapshot_path")
        if not snapshot_path:
            rollback_dir = PROJECT_ROOT / "qianqiu_os" / "runtime_governance" / "rollback_snapshots"
            candidates = sorted(
                p for p in rollback_dir.glob("delegation_active_config_*.json")
                if "pre_rollback" not in p.name
            )
            self.assertTrue(len(candidates) > 0)
            snapshot_path = str(candidates[-1])

        payload_new = {
            "operator_id": "rollback_test_operator_new",
            "operator_name": "rollback_test_operator_new",
            "change_reason": "rollback_test_new_save",
            "config_version": "rollback_test_new",
            "applied_preset": "L4_full_auto_send_safe"
        }
        result_new = service.save_config(payload_new)
        self.assertTrue(result_new["success"])

        active_path = PROJECT_ROOT / "qianqiu_os" / "runtime_governance" / "delegation_active_config.json"
        with open(active_path, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        current_preview = build_preview(current_data)
        self.assertEqual(current_preview["delegation_stage"], "L4_full_auto_send")
        self.assertEqual(current_preview["permission_level"], "L4")

        rollback_service = H5DelegationConfigRollbackV1()
        rollback_result = rollback_service.rollback_to_snapshot(
            snapshot_path=snapshot_path,
            operator_id="rollback_regression_operator",
            operator_name="rollback_regression_operator",
            change_reason="regression_rollback_check"
        )
        self.assertTrue(rollback_result["success"])

        with open(active_path, "r", encoding="utf-8") as f:
            restored_data = json.load(f)
        restored_preview = build_preview(restored_data)

        self.assertEqual(restored_preview["delegation_stage"], "L3_small_autonomy")
        self.assertEqual(restored_preview["permission_level"], "L3")

    def test_route_skeleton_minimum_chain(self):
        save_payload = {
            "operator_id": "route_regression_operator",
            "operator_name": "route_regression_operator",
            "change_reason": "route_regression_save",
            "config_version": "route_regression_v1",
            "applied_preset": "L3_small_autonomy_safe"
        }

        save_result = api_save_delegation_config(save_payload)
        self.assertTrue(save_result["success"])
        self.assertEqual(save_result["applied_preset"], "L3_small_autonomy_safe")

        preview_result = api_get_active_delegation_preview()
        self.assertTrue(preview_result["success"])
        self.assertEqual(preview_result["message"], "active preview loaded")
        self.assertEqual(preview_result["data"]["applied_preset"], "L3_small_autonomy_safe")
        self.assertEqual(preview_result["data"]["delegation_stage"], "L3_small_autonomy")
        self.assertEqual(preview_result["data"]["permission_level"], "L3")

        snapshot_result = api_list_delegation_snapshots()
        self.assertTrue(snapshot_result["success"])
        self.assertEqual(snapshot_result["message"], "snapshot list loaded")
        self.assertTrue(len(snapshot_result["items"]) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
