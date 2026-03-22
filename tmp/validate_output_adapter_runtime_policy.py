import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.output_adapter import OutputAdapter

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
        "user_id": "wa_user_001"
    },
    "input_context": {
        "source": "whatsapp_mock",
        "message_text": "Can I import a 2018 petrol SUV into Kenya?",
        "metadata": {
            "channel": "whatsapp",
            "session_id": "wa_session_001"
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
        "policy_summary": "This is a test summary for runtime delegation policy injection.",
        "manual_review_required": False,
        "warnings": [],
        "missing_fields": []
    },
    "wolong_result": {
        "customer_reply_result": {
            "reply_text": "This is a test reply."
        },
        "manual_review_result": {
            "manual_review_required": False
        },
        "business_action_result": {},
        "delegation_policy_result": {}
    }
}

formatted_output = adapter.format_output(
    source="whatsapp_mock",
    result=result,
)

policy = formatted_output.get("delegation_policy", {}) or {}

preview = {
    "target_source": formatted_output.get("target_source"),
    "reply_status": formatted_output.get("reply_status"),
    "outbound_ready": formatted_output.get("outbound_ready"),
    "delegation_master_switch": policy.get("delegation_master_switch"),
    "delegation_enabled": policy.get("delegation_enabled"),
    "delegation_stage": policy.get("delegation_stage"),
    "permission_level": policy.get("permission_level"),
    "allowed_time_windows": policy.get("allowed_time_windows"),
    "allowed_channels": policy.get("allowed_channels"),
    "allowed_actions": policy.get("allowed_actions"),
    "risk_levels_allowed": policy.get("risk_levels_allowed"),
    "business_stages_allowed": policy.get("business_stages_allowed"),
    "manual_review_required": policy.get("manual_review_required"),
    "human_supervision_mode": policy.get("human_supervision_mode"),
    "audit_required": policy.get("audit_required"),
    "rollback_enabled": policy.get("rollback_enabled"),
    "next_action": policy.get("next_action"),
    "business_stage": policy.get("business_stage"),
    "risk_level": policy.get("risk_level"),
    "destination_country": policy.get("destination_country")
}

print(json.dumps(preview, ensure_ascii=False, indent=2))
