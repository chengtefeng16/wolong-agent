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
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"
OUTPUT_SAMPLE_PATH = BASE_DIR / "runtime_governance" / "human_loop" / "human_loop_decision_v1.json"


class RuntimeHumanLoopGuardV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def evaluate(self, payload=None):
        payload = payload or {}

        active_config = self._read_json(ACTIVE_CONFIG_PATH) or {}
        whatsapp_control = active_config.get("whatsapp_control", {}) or {}
        delegation_policy = active_config.get("delegation_policy", {}) or {}

        requested_action = payload.get("requested_action") or "customer_send"
        risk_level = payload.get("risk_level") or delegation_policy.get("risk_level") or "unknown"
        business_stage = payload.get("business_stage") or delegation_policy.get("business_stage") or "unknown"
        source = payload.get("source") or "whatsapp"

        final_decision = "allow_readonly"
        reason = "readonly_baseline"
        human_confirmation_required = True

        ingress_mode = whatsapp_control.get("ingress_mode", "readonly")
        auto_reply = whatsapp_control.get("auto_reply", False)
        auto_dispatch = whatsapp_control.get("auto_dispatch", False)

        if ingress_mode == "off":
            final_decision = "blocked"
            reason = "channel_off"
            human_confirmation_required = True

        elif ingress_mode == "readonly":
            final_decision = "allow_readonly"
            reason = "readonly_mode_active"
            human_confirmation_required = True

        elif ingress_mode == "manual":
            final_decision = "human_decide"
            reason = "manual_mode_active"
            human_confirmation_required = True

        if requested_action in {"customer_send", "auto_send", "dispatch"}:
            if auto_reply or auto_dispatch:
                final_decision = "human_decide"
                reason = "auto_output_should_not_bypass_human"
                human_confirmation_required = True

        if risk_level in {"medium", "high", "unknown"}:
            final_decision = "human_decide"
            reason = f"risk_level_{risk_level}_requires_human_confirmation"
            human_confirmation_required = True

        if business_stage in {"negotiating", "quoted", "deal_closing"}:
            final_decision = "human_decide"
            reason = f"business_stage_{business_stage}_requires_human_confirmation"
            human_confirmation_required = True

        result = {
            "checked_at": self._now_str(),
            "source": source,
            "requested_action": requested_action,
            "risk_level": risk_level,
            "business_stage": business_stage,
            "whatsapp_control": whatsapp_control,
            "human_confirmation_required": human_confirmation_required,
            "final_decision": final_decision,
            "reason": reason,
            "human_final_authority": True,
        }

        self._write_json(OUTPUT_SAMPLE_PATH, result)
        return result


if __name__ == "__main__":
    guard = RuntimeHumanLoopGuardV1()
    demo_payload = {
        "requested_action": "customer_send",
        "risk_level": "medium",
        "business_stage": "negotiating",
        "source": "whatsapp",
    }
    print(json.dumps(guard.evaluate(demo_payload), ensure_ascii=False, indent=2))
