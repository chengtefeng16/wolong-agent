import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.manual_takeover_handler_v1 import ManualTakeoverHandlerV1

design_path = PROJECT_ROOT / "qianqiu_os" / "WOLONG_MANUAL_TAKEOVER_FLOW_V1.md"

handler = ManualTakeoverHandlerV1()
ticket_result = handler.create_ticket(
    trace_id="trace_demo_takeover_001",
    customer_id="cust_demo_001",
    session_id="wa_session_demo_001",
    channel="whatsapp",
    send_text="Hello from Wolong manual takeover flow.",
    business_context={
        "business_stage": "negotiating",
        "risk_level": "low",
        "emotion_state": "calm"
    },
    delegation_decision={
        "allow_real_send": False,
        "reason": "adapter_disabled",
        "priority_level": "manual_takeover_needed"
    },
    delivery_result={
        "success": False,
        "delivery_status": "pending_manual",
        "error_code": "adapter_disabled",
        "fallback_action": "human_review"
    },
    fallback_action="human_review",
)

result = {
    "design_exists": design_path.exists(),
    "ticket_result": ticket_result
}

print(json.dumps(result, ensure_ascii=False, indent=2))
