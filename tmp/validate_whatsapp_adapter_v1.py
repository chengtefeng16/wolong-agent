import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.real_channel_adapter_v1 import RealChannelAdapterV1

design_path = PROJECT_ROOT / "qianqiu_os" / "WOLONG_WHATSAPP_CHANNEL_ADAPTER_V1.md"

adapter = RealChannelAdapterV1()
result = adapter.send(
    {
        "channel": "whatsapp",
        "customer_id": "cust_demo_001",
        "session_id": "wa_session_demo_001",
        "send_text": "Hello from WhatsApp adapter validation."
    }
)

output = {
    "design_exists": design_path.exists(),
    "adapter_result": result
}

print(json.dumps(output, ensure_ascii=False, indent=2))
