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
PROMOTION_OUTPUT_PATH = BASE_DIR / "runtime_governance" / "promotion" / "promotion_guard_result_v1.json"


class RuntimePromotionGuardV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def evaluate(self, payload=None):
        payload = payload or {}

        promotion_master_switch = payload.get("promotion_master_switch", False)
        gray_release_enabled = payload.get("gray_release_enabled", True)
        human_final_confirmation = payload.get("human_final_confirmation", True)
        daily_limit = payload.get("daily_limit", 20)
        whitelist_enabled = payload.get("whitelist_enabled", True)
        rollback_enabled = payload.get("rollback_enabled", True)
        audit_required = payload.get("audit_required", True)
        requested_action = payload.get("requested_action", "promotion_send")

        final_decision = "blocked"
        reason = "promotion_master_switch_off"

        if not promotion_master_switch:
            final_decision = "blocked"
            reason = "promotion_master_switch_off"
        elif not human_final_confirmation:
            final_decision = "blocked"
            reason = "human_final_confirmation_required"
        elif requested_action != "promotion_send":
            final_decision = "blocked"
            reason = "unsupported_promotion_action"
        elif gray_release_enabled and whitelist_enabled and rollback_enabled and audit_required:
            final_decision = "allow_gray_only"
            reason = "gray_release_only_with_human_confirmation"
        else:
            final_decision = "human_decide"
            reason = "promotion_requires_manual_review"

        result = {
            "checked_at": self._now_str(),
            "requested_action": requested_action,
            "promotion_master_switch": promotion_master_switch,
            "gray_release_enabled": gray_release_enabled,
            "human_final_confirmation": human_final_confirmation,
            "daily_limit": daily_limit,
            "whitelist_enabled": whitelist_enabled,
            "rollback_enabled": rollback_enabled,
            "audit_required": audit_required,
            "final_decision": final_decision,
            "reason": reason,
            "safe_principle": "promotion_never_bypasses_human_final_authority",
        }

        self._write_json(PROMOTION_OUTPUT_PATH, result)
        return result


if __name__ == "__main__":
    guard = RuntimePromotionGuardV1()
    demo_payload = {
        "promotion_master_switch": False,
        "gray_release_enabled": True,
        "human_final_confirmation": True,
        "daily_limit": 20,
        "whitelist_enabled": True,
        "rollback_enabled": True,
        "audit_required": True,
        "requested_action": "promotion_send",
    }
    print(json.dumps(guard.evaluate(demo_payload), ensure_ascii=False, indent=2))
