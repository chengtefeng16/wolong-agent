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
from pathlib import Path

REPLIES_PATH = Path("knowledge/replies/en.json")


def load_replies():
    return json.loads(REPLIES_PATH.read_text(encoding="utf-8"))


def detect_language(message: str) -> str:
    for ch in message:
        if '\u4e00' <= ch <= '\u9fff':
            return "zh"

    if any(word in message for word in ["مرحبا", "سلام", "نموذج"]):
        return "ar"

    if any(word in message.lower() for word in ["hola", "formulario"]):
        return "es"

    if any(word in message.lower() for word in ["bonjour", "formulaire"]):
        return "fr"

    if any(word in message for word in ["Привет", "форма"]):
        return "ru"

    return "en"


def detect_intent(message: str):
    msg = message.lower()

    if any(word in msg for word in [
        "form", "filled",
        "表单", "填了",
        "formulario",
        "formulaire",
        "نموذج",
        "форма"
    ]):
        return "greeting_form"

    if any(word in msg for word in [
        "where", "location",
        "哪里", "在哪",
        "dónde",
        "où",
        "أين",
        "где"
    ]):
        return "ask_location"
    # L7.1 身份识别：个人
    if any(word in msg for word in [
        "individual", "private", "for myself",
        "个人", "自用",
        "particulier",
        "persona",
        "فرد",
        "частное"
    ]):
        return "identity_individual"

    # L7.1 身份识别：经销商
    if any(word in msg for word in [
        "dealer", "trader", "company", "reseller",
        "经销商", "车商", "公司",
        "concessionnaire",
        "comerciante",
        "تاجر",
        "дилер"
    ]):
        return "identity_dealer"

    return None


def reply_to_customer(message: str):
    replies = load_replies()

    # ① 识别语言
    lang = detect_language(message)

    # ② 识别意图
    intent_key = detect_intent(message)

    # ③ 没识别到意图 → 多语言兜底
    if not intent_key:
        fallback = {
            "en": "Thanks for your message. Could you please share a bit more detail?",
            "zh": "感谢你的消息，可以再多提供一点信息吗？",
            "ar": "شكرًا لرسالتك، هل يمكنك تزويدنا بمزيد من التفاصيل؟",
            "es": "Gracias por tu mensaje, ¿podrías proporcionar un poco más de detalle?",
            "fr": "Merci pour votre message, pourriez-vous fournir un peu plus de détails ?",
            "ru": "Спасибо за сообщение, не могли бы вы уточнить детали?"
        }
        return fallback.get(lang, fallback["en"])

    # ④ 取意图配置
    intent_block = replies.get(intent_key)
    if not intent_block:
        return fallback.get(lang, fallback["en"])

    # ⑤ 如果有 next_prompt（阶段推进优先）
    if "next_prompt" in intent_block:
        return intent_block["next_prompt"].get(
            lang,
            intent_block["next_prompt"].get("en")
        )

    # ⑥ 否则返回 replies
    if "replies" in intent_block:
        return intent_block["replies"].get(
            lang,
            intent_block["replies"].get("en")
        )

    return fallback.get(lang, fallback["en"])

if __name__ == "__main__":
    tests = [
        "I am an individual buyer",
        "我是个人买车",
        "We are a car dealer",
        "我们是汽车经销商"
    ]

    for t in tests:
        print("Customer:", t)
        print("AI:", reply_to_customer(t))
        print("-" * 40)

