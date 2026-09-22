"""
AI 服务层 — 封装 llm_gateway_v1.py（包含 thought-part 修复）。
llm_gateway_v1.py 已复制到本目录，SaaS 完全独立于 qianqiu_os。
"""
from __future__ import annotations

import asyncio
from typing import Any


async def generate_reply(
    customer_name: str,
    country: str,
    category: str,
    last_message: str,
    conversation_history: list[dict] | None = None,
) -> dict[str, Any]:
    from .llm_gateway_v1 import generate_reply as _sync_reply, _detect_customer_language

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _sync_reply(customer_name, country, category, last_message, conversation_history),
    )
    lang_code, _ = _detect_customer_language(last_message)
    result["language_code"] = lang_code
    return result
