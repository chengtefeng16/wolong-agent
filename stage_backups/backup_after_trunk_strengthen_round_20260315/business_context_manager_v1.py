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
import re
from typing import Any, Dict, List


class BusinessContextManagerV1:
    CAR_MODELS = [
        "prado", "camry", "lc300", "corolla", "rav4", "hilux", "land cruiser",
        "普拉多", "凯美瑞", "兰德酷路泽", "卡罗拉", "荣放", "海拉克斯",
    ]

    COUNTRIES = [
        "kazakhstan", "uzbekistan", "kyrgyzstan", "tajikistan", "russia",
        "哈萨克斯坦", "乌兹别克斯坦", "吉尔吉斯斯坦", "塔吉克斯坦", "俄罗斯",
    ]

    CONDITION_WORDS = [
        "used", "new", "left hand", "right hand", "petrol", "diesel",
        "二手", "新车", "左舵", "右舵", "汽油", "柴油",
    ]

    PRICE_WORDS = [
        "price", "budget", "usd", "$", "rmb", "报价", "预算", "美元", "人民币",
    ]

    def _normalize(self, text: str) -> str:
        return (text or "").strip().lower()

    def _find_keywords(self, text: str, words: List[str]) -> List[str]:
        text_lower = self._normalize(text)
        found = []
        for word in words:
            if word.lower() in text_lower:
                found.append(word)
        return list(dict.fromkeys(found))

    def _extract_quantity(self, text: str) -> int:
        nums = re.findall(r"\b\d+\b", text or "")
        if not nums:
            return 0
        try:
            return max(int(x) for x in nums)
        except Exception:
            return 0

    def _build_stage(self, models: List[str], destination: str, quantity: int, has_price_signal: bool) -> str:
        if models and destination and quantity >= 1 and has_price_signal:
            return "已进入报价准备"
        if models and destination and quantity >= 1:
            return "已进入需求确认"
        if models or destination:
            return "线索初步识别"
        return "待补充上下文"

    def _build_next_action(self, models: List[str], destination: str, quantity: int, has_price_signal: bool) -> str:
        if models and destination and quantity >= 1 and has_price_signal:
            return "建议人工尽快报价，并确认车况、年份、付款方式与物流路线。"
        if models and destination and quantity >= 1:
            return "建议继续追问预算、车况、年份和采购周期。"
        if models or destination:
            return "建议继续追问目标车型、数量和目的地国家。"
        return "建议先继续沟通，补齐车型、数量、国家等基础业务信息。"

    def build_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload or {}
        text = str(payload.get("text") or "").strip()
        if not text:
            return {
                "success": False,
                "error_code": "text_required",
                "error_message": "text is required",
            }

        models = self._find_keywords(text, self.CAR_MODELS)
        countries = self._find_keywords(text, self.COUNTRIES)
        conditions = self._find_keywords(text, self.CONDITION_WORDS)
        price_signals = self._find_keywords(text, self.PRICE_WORDS)
        quantity = self._extract_quantity(text)

        destination = countries[0] if countries else ""
        summary_parts = []

        if models:
            summary_parts.append(f"客户关注车型：{', '.join(models)}")
        if quantity:
            summary_parts.append(f"提到数量：{quantity}")
        if destination:
            summary_parts.append(f"目的地：{destination}")
        if conditions:
            summary_parts.append(f"条件关键词：{', '.join(conditions)}")
        if price_signals:
            summary_parts.append("客户已出现价格/预算相关信号")

        if not summary_parts:
            summary_parts.append("当前业务上下文仍较弱，尚未提取到明确车型、数量、国家或价格信号。")

        stage = self._build_stage(models, destination, quantity, bool(price_signals))
        next_action = self._build_next_action(models, destination, quantity, bool(price_signals))

        return {
            "success": True,
            "input_text": text,
            "models": models,
            "quantity": quantity,
            "destination_country": destination,
            "conditions": conditions,
            "price_signals": price_signals,
            "business_summary": "；".join(summary_parts),
            "business_stage": stage,
            "next_action": next_action,
        }


if __name__ == "__main__":
    demo_payload = {
        "text": "Hello, I need 5 Prado and 3 Camry for Kazakhstan market, please send price and used car options."
    }
    print(json.dumps(BusinessContextManagerV1().build_context(demo_payload), ensure_ascii=False, indent=2))
