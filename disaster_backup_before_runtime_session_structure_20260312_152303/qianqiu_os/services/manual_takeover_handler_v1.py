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


class ManualTakeoverHandlerV1:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1]
        self.base_dir = Path(base_dir)
        self.ticket_dir = self.base_dir / "runtime_governance" / "manual_takeover_tickets"
        self.ticket_dir.mkdir(parents=True, exist_ok=True)

    def create_ticket(
        self,
        trace_id,
        customer_id,
        session_id,
        channel,
        send_text,
        business_context,
        delegation_decision,
        delivery_result,
        fallback_action,
    ):
        ticket = {
            "ticket_type": "manual_takeover_v1",
            "ticket_id": f"takeover_{self._now_str()}",
            "status": "waiting_human_takeover",
            "created_at": self._now_str(),
            "trace_id": trace_id,
            "customer_id": customer_id,
            "session_id": session_id,
            "channel": channel,
            "original_send_text": send_text,
            "business_context": business_context or {},
            "delegation_decision": delegation_decision or {},
            "delivery_result": delivery_result or {},
            "fallback_action": fallback_action,
            "suggested_next_step": self._suggest_next_step(fallback_action),
        }

        path = self.ticket_dir / f"{ticket['ticket_id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "ticket_id": ticket["ticket_id"],
            "ticket_path": str(path),
            "status": ticket["status"],
            "suggested_next_step": ticket["suggested_next_step"],
        }

    def _suggest_next_step(self, fallback_action):
        mapping = {
            "human_review": "rewrite_and_send",
            "manual_takeover": "contact_manually",
            "draft_only": "hold_and_wait",
            "retry_later": "hold_and_wait",
        }
        return mapping.get(fallback_action, "hold_and_wait")

    def _now_str(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")
