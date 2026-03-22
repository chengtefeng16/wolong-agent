# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from __future__ import annotations

import json
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.whatsapp_provider_client_v1 import WhatsAppProviderClientV1


if __name__ == "__main__":
    client = WhatsAppProviderClientV1()
    readiness = client.readiness()

    result = {
        "success": True,
        "check_name": "real_channel_readiness_check_v1",
        "provider_readiness": readiness,
        "human_summary": {
            "ready_for_real_send": readiness.get("ready_for_real_send"),
            "ready_for_dry_run": readiness.get("ready_for_dry_run"),
            "missing_assets": readiness.get("missing_assets", []),
            "runtime_mode": readiness.get("runtime_mode"),
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
