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


class CustomerJudgementEngineV1:
    DEALER_KEYWORDS = [
        "dealer", "showroom", "reseller", "wholesale", "export", "import",
        "批发", "经销", "车商", "展厅", "贸易", "采购", "出口", "代理",
    ]

    BULK_KEYWORDS = [
        "units", "cars", "pcs", "container", "wholesale", "fleet",
        "台", "辆", "批量", "一批", "集装箱", "长期采购",
    ]

    PERSONAL_KEYWORDS = [
        "myself", "personal use", "family", "single car", "one car",
        "自用", "个人", "家用", "自己开", "一台", "一辆",
    ]

    INVALID_KEYWORDS = [
        "test", "hello", "hi", "ok", "thanks", "谢谢", "你好", "测试",
    ]

    CAR_MODEL_KEYWORDS = [
        "camry", "prado", "lc300", "corolla", "rav4", "hilux", "land cruiser",
        "凯美瑞", "普拉多", "兰德酷路泽", "卡罗拉", "荣放", "海拉克斯",
    ]

    COUNTRY_KEYWORDS = [
        "kazakhstan", "uzbekistan", "kyrgyzstan", "tajikistan", "russia",
        "哈萨克斯坦", "乌兹别克斯坦", "吉尔吉斯斯坦", "塔吉克斯坦", "俄罗斯",
    ]

    def _normalize_text(self, text: str) -> str:
        return (text or "").strip().lower()

    def _find_keywords(self, text: str, keywords: List[str]) -> List[str]:
        text_lower = self._normalize_text(text)
        found = []
        for kw in keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return found

    def _extract_quantity(self, text: str) -> int:
        numbers = re.findall(r"\b\d+\b", text or "")
        if not numbers:
            return 0
        try:
            return max(int(n) for n in numbers)
        except Exception:
            return 0

    def _judge_bucket(self, text: str) -> Dict[str, Any]:
        dealer_hits = self._find_keywords(text, self.DEALER_KEYWORDS)
        bulk_hits = self._find_keywords(text, self.BULK_KEYWORDS)
        personal_hits = self._find_keywords(text, self.PERSONAL_KEYWORDS)
        invalid_hits = self._find_keywords(text, self.INVALID_KEYWORDS)
        car_hits = self._find_keywords(text, self.CAR_MODEL_KEYWORDS)
        country_hits = self._find_keywords(text, self.COUNTRY_KEYWORDS)
        quantity = self._extract_quantity(text)

        reasons: List[str] = []
        judgement_keywords: List[str] = []

        judgement_keywords.extend(dealer_hits)
        judgement_keywords.extend(bulk_hits)
        judgement_keywords.extend(personal_hits)
        judgement_keywords.extend(car_hits)
        judgement_keywords.extend(country_hits)

        if invalid_hits and len(text.strip()) <= 12:
            reasons.append("消息内容过短，且更像测试/寒暄，不足以形成有效业务判断。")
            return {
                "bucket": "沟通无效",
                "confidence": "low",
                "keywords": judgement_keywords,
                "reason": "；".join(reasons),
                "needs_human_review": False,
                "priority": "low",
            }

        if dealer_hits:
            reasons.append("命中经销/贸易/批发类关键词，明显偏向车商或贸易型客户。")
        if bulk_hits:
            reasons.append("命中批量采购类关键词，存在多台车采购意图。")
        if quantity >= 3:
            reasons.append(f"消息中提到数量 {quantity}，更接近批量采购。")
        if car_hits:
            reasons.append("命中车型关键词，说明需求较明确。")
        if country_hits:
            reasons.append("命中国家/目的地关键词，具备跨境业务上下文。")
        if personal_hits:
            reasons.append("命中个人/自用类关键词，偏向个人客户。")

        if dealer_hits and (bulk_hits or quantity >= 3):
            bucket = "准车商"
            confidence = "high"
            needs_human_review = True
            priority = "high"
        elif dealer_hits or bulk_hits or quantity >= 3:
            bucket = "疑似车商"
            confidence = "medium"
            needs_human_review = True
            priority = "medium"
        elif personal_hits:
            bucket = "个人客户"
            confidence = "medium"
            needs_human_review = False
            priority = "medium"
        elif car_hits or country_hits:
            bucket = "待判断"
            confidence = "low"
            needs_human_review = True
            priority = "medium"
            if not reasons:
                reasons.append("存在业务线索，但暂不足以稳定归类。")
        else:
            bucket = "沟通无效"
            confidence = "low"
            needs_human_review = False
            priority = "low"
            if not reasons:
                reasons.append("未识别出明确业务意图。")

        return {
            "bucket": bucket,
            "confidence": confidence,
            "keywords": list(dict.fromkeys(judgement_keywords)),
            "reason": "；".join(reasons) if reasons else "暂无判断说明。",
            "needs_human_review": needs_human_review,
            "priority": priority,
        }

    def judge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = payload or {}
        text = str(payload.get("text") or "").strip()

        if not text:
            return {
                "success": False,
                "error_code": "text_required",
                "error_message": "text is required",
            }

        result = self._judge_bucket(text)
        return {
            "success": True,
            "input_text": text,
            "bucket": result["bucket"],
            "confidence": result["confidence"],
            "keywords": result["keywords"],
            "reason": result["reason"],
            "needs_human_review": result["needs_human_review"],
            "priority": result["priority"],
        }


if __name__ == "__main__":
    demo_payload = {
        "text": "Hello, I need 5 Prado and 3 Camry for Kazakhstan market, we do used car export."
    }
    print(json.dumps(CustomerJudgementEngineV1().judge(demo_payload), ensure_ascii=False, indent=2))
