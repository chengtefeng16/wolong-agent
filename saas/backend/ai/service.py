"""
AI 服务层 — 封装现有 llm_gateway_v1.py（包含 thought-part 修复）。
保持独立，方便后续替换模型或接入 CNcar 成本模块。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 让 saas/backend 能 import 项目根的 qianqiu_os
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


async def generate_reply(
    customer_name: str,
    country: str,
    category: str,
    last_message: str,
    conversation_history: list[dict] | None = None,
) -> dict[str, Any]:
    """
    异步包装 llm_gateway_v1.generate_reply（同步函数）。
    thought-part 修复已在 llm_gateway_v1.py 里，这里直接调用即可。
    """
    import asyncio
    from qianqiu_os.services.llm_gateway_v1 import generate_reply as _sync_reply, _detect_customer_language

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _sync_reply(customer_name, country, category, last_message, conversation_history),
    )

    # 补充语言信息
    lang_code, _ = _detect_customer_language(last_message)
    result["language_code"] = lang_code
    return result
