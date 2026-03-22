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
        "user_id": "wa_user_001",
        "customer_type": "dealer",
        "destination_country": "Kenya"
    },
    "input_context": {
        "source": "whatsapp_mock",
        "message_text": "Can I import a 2018 petrol SUV into Kenya?",
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
        "policy_summary": "This is a test summary for business context injection.",
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

preview = {
    "business_context": formatted_output.get("business_context"),
    "delegation_policy": {
        "business_stage": formatted_output.get("delegation_policy", {}).get("business_stage"),
        "risk_level": formatted_output.get("delegation_policy", {}).get("risk_level"),
        "destination_country": formatted_output.get("delegation_policy", {}).get("destination_country"),
        "customer_type": formatted_output.get("delegation_policy", {}).get("customer_type"),
        "intent_type": formatted_output.get("delegation_policy", {}).get("intent_type"),
        "emotion_state": formatted_output.get("delegation_policy", {}).get("emotion_state")
    }
}

print(json.dumps(preview, ensure_ascii=False, indent=2))
