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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.customer_judgement_engine_v1 import CustomerJudgementEngineV1
from qianqiu_os.services.business_context_manager_v1 import BusinessContextManagerV1


BASE_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class CustomerMemoryManagerV1:
    def __init__(self):
        self.judgement_engine = CustomerJudgementEngineV1()
        self.context_manager = BusinessContextManagerV1()

    def _memory_path(self, customer_id: str) -> Path:
        return MEMORY_DIR / f"{customer_id}.json"

    def update_memory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload or {}

        customer_id = str(payload.get("customer_id") or payload.get("phone") or "").strip()
        text = str(payload.get("text") or "").strip()

        if not customer_id:
            return {
                "success": False,
                "error_code": "customer_id_required",
                "error_message": "customer_id or phone is required",
            }

        if not text:
            return {
                "success": False,
                "error_code": "text_required",
                "error_message": "text is required",
            }

        memory_path = self._memory_path(customer_id)
        old_memory = _read_json(memory_path, {})

        if not isinstance(old_memory, dict) or not old_memory:
            old_memory = {
                "customer_id": customer_id,
                "created_at": _now_str(),
                "history": [],
            }

        judgement_result = self.judgement_engine.judge({"text": text})
        context_result = self.context_manager.build_context({"text": text})

        memory_record = {
            "updated_at": _now_str(),
            "latest_text": text,
            "customer_name": payload.get("customer_name") or old_memory.get("customer_name") or customer_id,
            "country": payload.get("country") or old_memory.get("country") or context_result.get("destination_country") or "",
            "bucket": judgement_result.get("bucket", "待判断"),
            "confidence": judgement_result.get("confidence", "low"),
            "judgement_keywords": judgement_result.get("keywords", []),
            "judgement_reason": judgement_result.get("reason", ""),
            "needs_human_review": judgement_result.get("needs_human_review", False),
            "priority": judgement_result.get("priority", "low"),
            "models": context_result.get("models", []),
            "quantity": context_result.get("quantity", 0),
            "destination_country": context_result.get("destination_country", ""),
            "conditions": context_result.get("conditions", []),
            "price_signals": context_result.get("price_signals", []),
            "business_summary": context_result.get("business_summary", ""),
            "business_stage": context_result.get("business_stage", ""),
            "next_action": context_result.get("next_action", ""),
        }

        old_memory["customer_id"] = customer_id
        old_memory["customer_name"] = memory_record["customer_name"]
        old_memory["country"] = memory_record["country"]
        old_memory["updated_at"] = memory_record["updated_at"]
        old_memory["latest_profile"] = memory_record

        history = old_memory.get("history", [])
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "time": _now_str(),
                "text": text,
                "bucket": memory_record["bucket"],
                "business_stage": memory_record["business_stage"],
                "next_action": memory_record["next_action"],
            }
        )

        old_memory["history"] = history[-20:]

        _write_json(memory_path, old_memory)

        return {
            "success": True,
            "customer_id": customer_id,
            "memory_path": str(memory_path),
            "latest_profile": memory_record,
            "history_count": len(old_memory["history"]),
        }


if __name__ == "__main__":
    demo_payload = {
        "customer_id": "customer_demo_001",
        "customer_name": "Demo Buyer",
        "country": "Kazakhstan",
        "text": "Hello, I need 5 Prado and 3 Camry for Kazakhstan market, please send price and used car options.",
    }
    print(json.dumps(CustomerMemoryManagerV1().update_memory(demo_payload), ensure_ascii=False, indent=2))
