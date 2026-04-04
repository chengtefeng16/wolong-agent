# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
# Project: AgentOS / Wolong Agent System
# ================================================================
"""
LLM 网关 V1 — 统一 AI 推理入口
优先级：Gemini（config.py GEMINI_API_KEY）> Claude（ANTHROPIC_API_KEY）> 规则兜底

职责：
  1. 统一出口：所有 AI 推理请求从这里出
  2. 上下文注入：自动将历史经验注入 prompt，提升回复质量
  3. 降级保底：无 key 或 API 报错时用规则兜底
  4. 使用记录：每次调用结果可写入 experience_store

运行环境：需要 .venv_delivery（google-genai >= 1.69 已安装）
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── 系统宪法/角色定义 ──
WOLONG_SYSTEM_PROMPT = """你是「卧龙 Agent」，一个专注于跨境二手车出口业务的智能客服助理。

你的核心职责：
1. 准确判断客户意图（是否为车商/个人/询价/询政策）
2. 用专业、友好的语气回复客户
3. 收集关键信息：目标国家、车型、数量、预算
4. 对不同国家客户使用合适的语言风格
5. 对准车商保持主动推进成交的节奏

回复原则：
- 简洁有力，不废话
- 专业但不冷漠
- 主动引导客户提供更多信息
- 如果是批量采购意图，保持热情跟进节奏

你服务的市场：中亚、中东、非洲、拉美的二手车进口商/车商/个人买家。
"""

CLASSIFY_SYSTEM_PROMPT = """你是「卧龙 Agent」的智能分类引擎。
根据客户消息，判断客户类型和意图。

分类标准：
- 准车商（dealer）：提到批量采购、月度采购、转售、dealer、我是车商
- 疑似车商：提到多辆车但不确定是否批量，或疑似有采购背景
- 个人客户：明确表示自用、家用、not for resale
- 沟通无效：广告、测试、垃圾信息

输出JSON格式：
{
  "bucket": "准车商|疑似车商|个人客户|沟通无效",
  "confidence": 0.0-1.0,
  "key_signals": ["信号1", "信号2"],
  "suggested_action": "建议动作说明"
}

只输出JSON，不要其他内容。"""


GEMINI_MODEL = "gemini-2.5-flash"

# 政策/法规类关键词 → 触发联网搜索模式
_POLICY_KEYWORDS = [
    "政策", "法规", "规定", "限制", "禁止", "能不能", "可以进", "能进", "允许",
    "年份", "车龄", "关税", "手续", "清关", "进口要求", "排放", "标准",
    "2020", "2021", "2022", "2023", "2024", "2025",
    "policy", "regulation", "import", "ban", "restriction", "age limit",
]

def _needs_search(message: str) -> bool:
    """判断消息是否需要联网搜索（政策/法规/年份限制等实时信息）"""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _POLICY_KEYWORDS)


def _load_gemini_key() -> Optional[str]:
    """从 config.py 或环境变量读取 GEMINI_API_KEY"""
    # 1. 优先读 config.py（项目根目录）
    try:
        import importlib.util
        config_path = PROJECT_ROOT / "config.py"
        if config_path.exists():
            spec = importlib.util.spec_from_file_location("_wolong_config", config_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            key = getattr(mod, "GEMINI_API_KEY", None)
            if key and key.strip():
                return key.strip()
    except Exception:
        pass
    # 2. 再读环境变量
    return os.getenv("GEMINI_API_KEY") or None


def _call_gemini_rest(api_key: str, prompt: str, system: str,
                      max_tokens: int, temperature: float,
                      enable_search: bool = False) -> Dict[str, Any]:
    """
    直接用 urllib 调用 Gemini REST API。
    绕过 httpx / google-genai SDK，避免系统代理截断响应的问题。
    enable_search=True → 启用 Google Search grounding（用于政策/法规实时查询）
    """
    import urllib.request
    import ssl

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    if enable_search:
        # 搜索模式：保留少量 thinking 帮助整合搜索结果，提高 token 上限
        gen_config = {
            "maxOutputTokens": max(max_tokens, 1200),
            "temperature": temperature,
            "thinkingConfig": {"thinkingBudget": 512},
        }
    else:
        # 普通对话模式：关闭 thinking，token 全给输出
        gen_config = {
            "maxOutputTokens": max(max_tokens, 800),
            "temperature": temperature,
            "thinkingConfig": {"thinkingBudget": 0},
        }

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }
    if enable_search:
        payload["tools"] = [{"googleSearch": {}}]
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # 系统代理有自签名证书 → 禁用 SSL 验证（与 wa_send_message 一致）
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    try:
        with opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            text = (
                body.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
            )
            return {"text": text, "source": "gemini", "error": None}
    except Exception as e:
        return {"text": None, "source": "api_error", "error": str(e)}


def _load_gemini_client():
    """懒加载 google-genai client（备用，主路径改用 _call_gemini_rest）"""
    api_key = _load_gemini_key()
    if not api_key:
        return None, "未设置 GEMINI_API_KEY"
    return True, None   # 有 key 即视为可用，实际调用走 _call_gemini_rest


def _load_anthropic_client():
    """懒加载 Anthropic client，失败时返回 (None, error_msg)"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "未设置 ANTHROPIC_API_KEY"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        return client, None
    except ImportError:
        return None, "anthropic SDK 未安装"
    except Exception as e:
        return None, str(e)


def call_llm(
    prompt: str,
    system: str = WOLONG_SYSTEM_PROMPT,
    max_tokens: int = 600,
    temperature: float = 0.7,
    model: str = GEMINI_MODEL,
    enable_search: bool = False,
) -> Dict[str, Any]:
    """
    统一 LLM 调用入口。优先 Gemini，其次 Claude，最后规则兜底。
    返回: {"text": str, "source": "gemini"|"claude"|"no_key"|"api_error", "error": str|None}
    """
    # ── 1. 尝试 Gemini（走 urllib REST，绕过 httpx/代理截断问题）──
    gemini_client, gemini_err = _load_gemini_client()
    if gemini_client is not None:
        api_key = _load_gemini_key()
        result = _call_gemini_rest(api_key, prompt, system, max_tokens, temperature,
                                   enable_search=enable_search)
        if result["text"]:
            if enable_search:
                result["source"] = "gemini+search"
            return result
        gemini_err = result.get("error", "gemini REST 调用失败")
        print(f"[LLM][Gemini ERROR] {gemini_err}", flush=True)

    # ── 2. 降级到 Claude ──
    anthropic_client, anthropic_err = _load_anthropic_client()
    if anthropic_client is not None:
        try:
            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text if message.content else ""
            return {"text": text, "source": "claude", "error": None}
        except Exception as e:
            return {"text": None, "source": "api_error", "error": str(e)}

    # ── 3. 无可用 key ──
    return {"text": None, "source": "no_key", "error": gemini_err or anthropic_err}


def generate_reply(
    customer_name: str,
    country: str,
    category: str,
    last_message: str,
    conversation_history: List[Dict] = None,
    experience_examples: List[Dict] = None,
) -> Dict[str, Any]:
    """
    生成客户回复建议。
    自动注入经验示例提升质量。
    """
    if not last_message.strip():
        return {"suggested_reply": "", "source": "empty_input", "error": "消息为空"}

    # 构建 prompt
    history_text = ""
    if conversation_history:
        last_5 = conversation_history[-5:]
        history_text = "\n".join([
            f"{'客户' if m.get('role') in ('customer','客户') else '我方'}：{m.get('text','')}"
            for m in last_5
        ])

    experience_text = ""
    if experience_examples:
        examples = experience_examples[:3]
        experience_text = "\n\n【历史成功经验参考（请从中学习回复风格）】\n"
        for i, ex in enumerate(examples, 1):
            experience_text += (
                f"案例{i}：客户说「{ex.get('customer_msg','')}」\n"
                f"  成功回复：「{ex.get('approved_reply','')}」\n"
                f"  效果：{ex.get('outcome','positive')}\n"
            )

    # 有对话历史时是"进行中的对话"，直接回应内容，不加"您好，[名字]！"前缀
    is_ongoing = bool(history_text)
    reply_instruction = (
        "这是一段正在进行中的对话。请直接针对客户最新消息给出回复，"
        "不要再重复'您好'或客户名称作为开头，自然地延续对话。"
        if is_ongoing else
        "这是与新客户的第一次对话，可以礼貌问候后直接引导到车辆需求。"
    )

    prompt = f"""客户背景：
- 客户类型：{category}
- 目标市场：{country}

{"对话记录：" + chr(10) + history_text if is_ongoing else "（首次接触）"}

客户最新消息：「{last_message}」
{experience_text}

{reply_instruction}
回复要求：
- 必须围绕跨境二手车出口业务
- 简洁自然，不超过100字
- 直接给出回复内容，不加任何说明或前缀标注"""

    # 政策/年份/法规类问题 → 启用 Google Search 联网搜索
    use_search = _needs_search(last_message)
    if use_search:
        print(f"[LLM] 检测到政策类查询，启用联网搜索: {last_message[:40]}", flush=True)

    result = call_llm(prompt, system=WOLONG_SYSTEM_PROMPT, max_tokens=400,
                      enable_search=use_search)

    if result["text"]:
        return {
            "suggested_reply": result["text"].strip(),
            "source": result["source"],
            "error": None,
        }

    # 降级：规则模板
    fallback = _rule_based_reply(customer_name, country, category, last_message)
    return {
        "suggested_reply": fallback,
        "source": "rule_fallback",
        "error": result.get("error"),
    }


def classify_customer(last_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    用 LLM 判断客户类型。
    返回: {"bucket": str, "confidence": float, "key_signals": list, "source": str}
    """
    history_text = ""
    if conversation_history:
        last_3 = conversation_history[-3:]
        history_text = "\n".join([
            f"{'客户' if m.get('role') in ('customer','客户') else '我方'}：{m.get('text','')}"
            for m in last_3
        ])

    prompt = f"""历史对话：
{history_text or '（无）'}

最新消息：「{last_message}」

请判断客户类型并输出JSON。"""

    result = call_llm(prompt, system=CLASSIFY_SYSTEM_PROMPT, max_tokens=200, temperature=0.3)

    if result["text"]:
        try:
            # 提取 JSON（LLM 可能输出其他内容）
            text = result["text"].strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                data["source"] = result["source"]
                return data
        except Exception:
            pass

    # 降级：规则分类
    return _rule_based_classify(last_message)


def _rule_based_reply(customer_name: str, country: str, category: str, last_message: str) -> str:
    """规则兜底回复（LLM 不可用时）"""
    msg = last_message.lower()
    if any(w in msg for w in ["price", "cost", "quote", "how much", "报价", "多少钱"]):
        return (f"Hi {customer_name}, thank you for your interest! "
                f"We offer very competitive prices for the {country} market. "
                f"Could you tell us which vehicle models you're looking for and your target quantity? "
                f"We'll prepare a detailed quotation within 24 hours.")
    elif any(w in msg for w in ["suv", "sedan", "pickup", "van", "car", "vehicle"]):
        return (f"Hi {customer_name}, great choice! "
                f"We have an excellent selection of vehicles well-suited for {country}. "
                f"What quantity are you looking for, and do you have specific brand preferences?")
    elif any(w in msg for w in ["ship", "delivery", "logistics", "物流", "运费"]):
        return (f"Hi {customer_name}, we handle full shipping to {country}. "
                f"Sea freight typically takes 25–45 days. "
                f"Shall we include shipping in our quotation?")
    elif any(w in msg for w in ["hello", "hi", "good", "您好", "你好"]):
        return (f"Hi {customer_name}! Welcome to Wolong Auto Export. "
                f"We specialize in vehicle exports to {country}. "
                f"How can we assist you today?")
    else:
        return (f"Hi {customer_name}, thank you for reaching out! "
                f"Please share your vehicle requirements for {country} "
                f"(model, quantity, budget) and we'll respond right away.")


def _rule_based_classify(last_message: str) -> Dict[str, Any]:
    """规则兜底分类"""
    msg = last_message.lower()
    if any(w in msg for w in ["dealer", "resale", "monthly", "regularly", "bulk", "wholesale", "我是车商", "批量"]):
        return {"bucket": "准车商", "confidence": 0.8, "key_signals": ["批量采购意图"], "source": "rule"}
    elif any(w in msg for w in ["units", "pieces", "vehicles", "辆", "台", "pcs"]):
        return {"bucket": "疑似车商", "confidence": 0.6, "key_signals": ["多辆询价"], "source": "rule"}
    elif any(w in msg for w in ["family", "personal", "myself", "自用", "家用", "not for resale"]):
        return {"bucket": "个人客户", "confidence": 0.85, "key_signals": ["个人自用"], "source": "rule"}
    else:
        return {"bucket": "疑似车商", "confidence": 0.4, "key_signals": ["信号不明确"], "source": "rule"}
