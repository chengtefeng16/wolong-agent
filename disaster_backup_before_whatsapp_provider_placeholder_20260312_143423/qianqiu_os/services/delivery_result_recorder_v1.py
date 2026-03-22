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
from datetime import datetime
from pathlib import Path


class DeliveryResultRecorderV1:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1]
        self.base_dir = Path(base_dir)
        self.log_dir = self.base_dir / "runtime_governance" / "delivery_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def record(self, pre_send_record, post_send_result):
        pre_send_record = pre_send_record or {}
        post_send_result = post_send_result or {}

        record = {
            "record_type": "delivery_result_loop_v1",
            "recorded_at": self._now_str(),
            "pre_send_record": pre_send_record,
            "post_send_result": post_send_result,
            "final_status": post_send_result.get("delivery_status"),
            "needs_manual_takeover": post_send_result.get("fallback_action") in ("human_review", "manual_takeover"),
        }

        path = self.log_dir / f"delivery_result_{self._now_str()}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "record_path": str(path),
            "final_status": record["final_status"],
            "needs_manual_takeover": record["needs_manual_takeover"],
        }

    def _now_str(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")
