import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.delivery_result_recorder_v1 import DeliveryResultRecorderV1

design_path = PROJECT_ROOT / "qianqiu_os" / "WOLONG_DELIVERY_RESULT_LOOP_DESIGN_V1.md"

recorder = DeliveryResultRecorderV1()

pre_send_record = {
    "trace_id": "trace_demo_001",
    "channel": "whatsapp",
    "customer_id": "cust_demo_001",
    "session_id": "wa_session_demo_001",
    "send_text": "Hello from Wolong.",
    "business_context": {
        "business_stage": "negotiating",
        "risk_level": "low",
        "emotion_state": "calm"
    },
    "delegation_decision": {
        "allow_real_send": True,
        "reason": "delegation_policy_passed",
        "priority_level": "passed"
    },
    "config_version": "demo_v1",
    "applied_preset": "L3_small_autonomy_safe"
}

post_send_result = {
    "success": False,
    "channel": "whatsapp",
    "delivery_status": "pending_manual",
    "provider_message_id": None,
    "error_code": "adapter_disabled",
    "error_message": "real channel adapter is disabled",
    "retryable": False,
    "fallback_action": "human_review"
}

record_result = recorder.record(pre_send_record, post_send_result)

result = {
    "design_exists": design_path.exists(),
    "record_result": record_result
}

print(json.dumps(result, ensure_ascii=False, indent=2))
