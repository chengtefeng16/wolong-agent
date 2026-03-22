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
import re
import sys
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_whatsapp.json"
OUTPUT_JSON_PATH = BASE_DIR / "runtime_views" / "business_judgement" / "wolong_business_judgement_v1.json"
OUTPUT_MD_PATH = BASE_DIR / "project_memory" / "WOLONG_BUSINESS_JUDGEMENT_SUMMARY_20260314.md"


class WolongBusinessJudgementV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _write_text(self, path: Path, text: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _extract_keywords(self, text: str):
        text = (text or "").lower()
        candidates = []
        for kw in ["prado", "camry", "suv", "units", "regularly", "price", "prices", "buy", "export", "supply"]:
            if kw in text:
                candidates.append(kw)
        if re.search(r"\b\d+\b", text):
            candidates.append("quantity_signal")
        return sorted(set(candidates))

    def _judge_customer_type(self, bucket: str, latest_message: str):
        msg = (latest_message or "").lower()
        if bucket == "准车商":
            return "dealer"
        if "regularly" in msg or "units" in msg or "supply" in msg:
            return "dealer_like"
        if bucket == "疑似车商":
            return "dealer_like"
        if bucket == "个人客户":
            return "individual"
        return "unknown"

    def _judge_business_stage(self, latest_message: str):
        msg = (latest_message or "").lower()
        if any(x in msg for x in ["need", "quote", "price", "prices"]):
            return "quoted"
        if any(x in msg for x in ["buy regularly", "regularly", "monthly", "stable supply"]):
            return "negotiating"
        return "lead"

    def _judge_risk_level(self, bucket: str, latest_message: str):
        msg = (latest_message or "").lower()
        if bucket == "无效沟通":
            return "low"
        if "regularly" in msg or re.search(r"\b[5-9]\b|\b[1-9]\d+\b", msg):
            return "medium"
        if bucket == "疑似车商":
            return "medium"
        return "low"

    def _judge_intent_type(self, latest_message: str):
        msg = (latest_message or "").lower()
        if any(x in msg for x in ["prado", "camry", "suv"]):
            return "vehicle_purchase"
        if "price" in msg or "prices" in msg:
            return "quotation_request"
        return "general_inquiry"

    def _next_best_action(self, customer_type: str, business_stage: str, risk_level: str):
        if risk_level in {"medium", "high"}:
            return "human_follow_up"
        if business_stage == "quoted":
            return "send_structured_quote"
        if customer_type in {"dealer", "dealer_like"}:
            return "confirm_volume_and_destination"
        return "clarify_need"

    def _follow_up_questions(self, customer_type: str, intent_type: str):
        questions = []
        if customer_type in {"dealer", "dealer_like"}:
            questions.append("请确认您是展厅/经销商采购还是项目采购？")
            questions.append("请确认首批数量、长期月需求和目的国。")
        else:
            questions.append("请确认您是自用还是转售用途。")
        if intent_type == "vehicle_purchase":
            questions.append("请确认目标车型、年份范围和预算。")
            questions.append("请确认是否接受中国境内交车价与口岸交车价两套报价。")
        else:
            questions.append("请确认您现在最想先了解的是价格、车型还是出口流程。")
        return questions

    def build(self):
        data = self._read_json(SOURCE_PATH)
        recent_focus = data.get("recent_focus", []) or []

        items = []
        for item in recent_focus:
            phone = item.get("phone")
            customer_name = item.get("customer_name")
            bucket = item.get("bucket")
            latest_message = item.get("latest_message", "")

            customer_type = self._judge_customer_type(bucket, latest_message)
            business_stage = self._judge_business_stage(latest_message)
            risk_level = self._judge_risk_level(bucket, latest_message)
            intent_type = self._judge_intent_type(latest_message)
            next_best_action = self._next_best_action(customer_type, business_stage, risk_level)
            follow_up_questions = self._follow_up_questions(customer_type, intent_type)
            reason_keywords = self._extract_keywords(latest_message)
            handoff_recommended = risk_level in {"medium", "high"} or business_stage in {"negotiating", "quoted"}

            items.append({
                "phone": phone,
                "customer_name": customer_name,
                "bucket": bucket,
                "latest_message": latest_message,
                "customer_type": customer_type,
                "business_stage": business_stage,
                "risk_level": risk_level,
                "intent_type": intent_type,
                "next_best_action": next_best_action,
                "follow_up_questions": follow_up_questions,
                "handoff_recommended": handoff_recommended,
                "reason_keywords": reason_keywords,
            })

        result = {
            "generated_at": self._now_str(),
            "source_path": str(SOURCE_PATH),
            "count": len(items),
            "items": items,
            "conclusion": "卧龙 Agent 已具备最小业务判断力增强骨架，可对重点客户给出客户类型、业务阶段、风险等级、下一步动作与补问建议。",
        }

        md_lines = [
            "# WOLONG BUSINESS JUDGEMENT SUMMARY · 2026-03-14",
            "",
            f"- generated_at: {result['generated_at']}",
            f"- source_path: {result['source_path']}",
            f"- count: {result['count']}",
            "",
        ]

        for item in items:
            md_lines.extend([
                f"## {item.get('customer_name')} / {item.get('phone')}",
                f"- bucket: {item.get('bucket')}",
                f"- customer_type: {item.get('customer_type')}",
                f"- business_stage: {item.get('business_stage')}",
                f"- risk_level: {item.get('risk_level')}",
                f"- intent_type: {item.get('intent_type')}",
                f"- next_best_action: {item.get('next_best_action')}",
                f"- handoff_recommended: {item.get('handoff_recommended')}",
                f"- reason_keywords: {', '.join(item.get('reason_keywords', [])) if item.get('reason_keywords') else 'none'}",
                "- follow_up_questions:",
            ])
            for q in item.get("follow_up_questions", []):
                md_lines.append(f"  - {q}")
            md_lines.append("")

        md_lines.extend([
            "## 结论",
            result["conclusion"],
            "",
        ])

        self._write_json(OUTPUT_JSON_PATH, result)
        self._write_text(OUTPUT_MD_PATH, "\n".join(md_lines))
        return result


if __name__ == "__main__":
    print(json.dumps(WolongBusinessJudgementV1().build(), ensure_ascii=False, indent=2))
