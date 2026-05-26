# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
# Project: AgentOS / Wolong Agent System
# ================================================================
"""
历史客户重新激活分析器 V1

功能：
  1. 解析 WhatsApp 导出的 .txt 聊天记录
  2. 用 Gemini 分析每个客户：姓名、国家、询问车型、意向等级、未成交原因
  3. 自动生成个性化的英文重新激活消息
  4. 结果持久化到 runtime_reactivation/ 目录

WhatsApp 导出格式支持：
  [MM/DD/YY, HH:MM:SS AM] Name: text
  MM/DD/YYYY, HH:MM - Name: text
  [YYYY/MM/DD HH:MM:SS] Name: text
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REACTIVATION_DIR = PROJECT_ROOT / "qianqiu_os" / "runtime_reactivation"

# ── 意向等级定义 ──
INTENT_LEVELS = {
    "hot": "🔥 高意向（曾明确询价/谈条件）",
    "warm": "🟡 中意向（有询问但未深入）",
    "cold": "🧊 低意向（仅闲聊/无明确需求）",
    "unknown": "❓ 无法判断",
}


# ─────────────────────────────────────────
# 1. TXT 解析器
# ─────────────────────────────────────────

def parse_whatsapp_export(text: str, my_name_hint: str = "") -> Dict[str, Any]:
    """
    解析 WhatsApp 导出 TXT，返回结构化对话数据。
    自动识别"我方"和"客户"两个角色。

    Returns:
        {
          "participants": ["Alice", "Me"],
          "messages": [
            {"time": "2024-01-15 14:30", "sender": "Alice", "text": "Hello"},
            ...
          ],
          "customer_name": "Alice",
          "my_name": "Me",
          "raw_count": 42,
        }
    """
    lines = text.splitlines()
    messages = []

    # 常见 WhatsApp 时间戳格式
    patterns = [
        # [2026/3/18 19:43:54] ~Name: text  ← 中文版导出（年/月/日 时:分:秒，无逗号）
        re.compile(
            r'^\[(\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\]\s+~?([^:]+):\s*(.*)$'
        ),
        # [1/15/24, 2:30:45 PM] Name: text  ← 英文版导出（月/日/年, 时:分:秒 AM/PM）
        re.compile(
            r'^\[(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s+~?([^:]+):\s*(.*)$',
            re.IGNORECASE
        ),
        # 1/15/2024, 14:30 - Name: text
        re.compile(
            r'^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*~?([^:]+):\s*(.*)$'
        ),
        # [2024-01-15 14:30:00] Name: text
        re.compile(
            r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\]\s+~?([^:]+):\s*(.*)$'
        ),
        # 2024-01-15, 14:30 - Name: text
        re.compile(
            r'^(\d{4}-\d{2}-\d{2},\s*\d{2}:\d{2}(?::\d{2})?)\s*-\s*~?([^:]+):\s*(.*)$'
        ),
    ]

    current_msg = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched = False
        for pat in patterns:
            m = pat.match(line)
            if m:
                if current_msg:
                    messages.append(current_msg)
                time_str = m.group(1).strip()
                sender = m.group(2).strip()
                text = m.group(3).strip()
                # 跳过系统消息（WhatsApp 加密提示、广告发起提示等）
                _SYSTEM_MSGS = (
                    "messages and calls are end-to-end encrypted",
                    "this chat is with a business account",
                    "消息和通话已进行端到端加密",
                    "此聊天从 facebook 或 instagram 广告发起",
                    "此聊天从facebook或instagram广告发起",
                )
                _text_lower = text.lower().strip('\u200e\u200f\u202a\u202c ')
                if any(s in _text_lower for s in _SYSTEM_MSGS) or not _text_lower:
                    current_msg = None
                    matched = True
                    break
                current_msg = {"time": time_str, "sender": sender, "text": text}
                matched = True
                break

        if not matched and current_msg:
            # 多行消息续行
            current_msg["text"] += "\n" + line

    if current_msg:
        messages.append(current_msg)

    if not messages:
        return {
            "participants": [],
            "messages": [],
            "customer_name": "",
            "my_name": "",
            "raw_count": 0,
            "error": "未能解析任何消息，请确认文件格式为 WhatsApp 导出的 .txt 文件",
        }

    # ── 识别参与者 ──
    sender_counts: Dict[str, int] = {}
    for msg in messages:
        s = msg["sender"]
        sender_counts[s] = sender_counts.get(s, 0) + 1

    participants = sorted(sender_counts.keys(), key=lambda x: -sender_counts[x])

    # 我方识别：消息数量较少的一方（业务员通常回复少于客户消息）
    # 如果 hint 提供了，优先匹配
    my_name = ""
    customer_name = ""

    if len(participants) >= 2:
        if my_name_hint:
            for p in participants:
                if my_name_hint.lower() in p.lower():
                    my_name = p
                    break
        if not my_name:
            # 默认：消息较少的那方为我方
            my_name = min(participants, key=lambda x: sender_counts[x])
        customer_name = next((p for p in participants if p != my_name), participants[0])
    elif len(participants) == 1:
        customer_name = participants[0]
        my_name = "我方"

    return {
        "participants": participants,
        "messages": messages,
        "customer_name": customer_name,
        "my_name": my_name,
        "raw_count": len(messages),
    }


# ─────────────────────────────────────────
# 2. Gemini 分析
# ─────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """You are a senior used-car export sales analyst.
Given a WhatsApp conversation between a salesperson and a customer, extract structured information and generate a personalized reactivation message.

Output ONLY valid JSON in this exact format:
{
  "customer_name": "...",
  "country": "...",
  "car_models_interested": ["model1", "model2"],
  "intent_level": "hot|warm|cold|unknown",
  "intent_reason": "one sentence explaining the intent level",
  "no_deal_reason": "why the deal didn't close (price, no response, budget, timing, etc.)",
  "last_contact_summary": "brief summary of last meaningful exchange",
  "reactivation_message": "personalized English message to re-engage this customer (2-4 sentences, friendly and professional, reference their specific interest)"
}

Rules:
- intent_level "hot": customer explicitly asked for price/quote/invoice or negotiated terms
- intent_level "warm": customer showed interest but no concrete steps
- intent_level "cold": only casual inquiry or stopped responding early
- reactivation_message must mention the specific car model(s) they asked about
- reactivation_message should feel natural, not spammy, reference a genuine reason to reconnect
- If country is unclear, infer from phone number prefix or language used
- Output only the JSON object, no markdown, no explanation"""


def _load_gemini_key() -> Optional[str]:
    try:
        import importlib.util
        config_path = PROJECT_ROOT / "config.py"
        if config_path.exists():
            spec = importlib.util.spec_from_file_location("_cfg", config_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            key = getattr(mod, "GEMINI_API_KEY", None)
            if key and key.strip():
                return key.strip()
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY") or None


def _call_gemini_for_analysis(conversation_text: str, customer_name: str) -> Dict[str, Any]:
    """调用 Gemini REST API 分析对话，返回结构化分析结果"""
    import urllib.request
    import ssl

    api_key = _load_gemini_key()
    if not api_key:
        return {"error": "GEMINI_API_KEY 未配置"}

    prompt = f"""Analyze this WhatsApp conversation with customer "{customer_name}":

--- CONVERSATION START ---
{conversation_text[:8000]}
--- CONVERSATION END ---

Extract the customer profile and generate a reactivation message."""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-preview-04-17:generateContent?key={api_key}"
    )

    payload = {
        "system_instruction": {"parts": [{"text": ANALYSIS_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.3,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    proxies = {
        "https": os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", "")),
        "http": os.environ.get("HTTP_PROXY", os.environ.get("http_proxy", "")),
    }
    proxy_handler = urllib.request.ProxyHandler({k: v for k, v in proxies.items() if v})
    https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
    opener = urllib.request.build_opener(proxy_handler, https_handler)

    last_error = ""
    for attempt in range(3):  # 最多重试3次
        if attempt > 0:
            time.sleep(3 * attempt)  # 3s, 6s 递增等待
        try:
            with opener.open(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                raw_text = (
                    body.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                )
                # 解析 JSON（有时 Gemini 会加 markdown 代码块）
                clean = raw_text.strip()
                if clean.startswith("```"):
                    clean = re.sub(r"^```(?:json)?\n?", "", clean)
                    clean = re.sub(r"\n?```$", "", clean)
                result = json.loads(clean)
                return result
        except json.JSONDecodeError as e:
            return {"error": f"Gemini 返回格式异常: {e}", "raw": raw_text[:500] if 'raw_text' in locals() else ""}
        except Exception as e:
            last_error = str(e)
            # 503/429/400(代理瞬断) 重试，其他错误直接返回
            if "503" in last_error or "429" in last_error or "400" in last_error or "timed out" in last_error.lower():
                print(f"[Reactivation] Gemini 暂时不可用，第 {attempt+1} 次重试... ({last_error})")
                continue
            return {"error": f"Gemini API 调用失败: {last_error}"}
    return {"error": f"Gemini API 重试3次后仍失败: {last_error}"}


def _format_conversation_for_gemini(parsed: Dict[str, Any], max_messages: int = 80) -> str:
    """将解析后的对话格式化为适合 Gemini 读取的文本"""
    messages = parsed["messages"]
    my_name = parsed["my_name"]
    customer_name = parsed["customer_name"]

    lines = []
    for msg in messages[-max_messages:]:  # 取最近的消息（避免超长）
        role = "SALESPERSON" if msg["sender"] == my_name else "CUSTOMER"
        text = msg["text"].strip()
        if text and text not in ("<Media omitted>", "image omitted", "video omitted",
                                  "audio omitted", "document omitted", "sticker omitted"):
            lines.append(f"[{msg['time']}] {role}: {text}")

    return "\n".join(lines)


# ─────────────────────────────────────────
# 3. 主分析入口
# ─────────────────────────────────────────

def analyze_chat_file(
    chat_text: str,
    filename: str = "chat.txt",
    my_name_hint: str = "",
    phone: str = "",
) -> Dict[str, Any]:
    """
    分析单个 WhatsApp 导出文件。

    Args:
        chat_text: TXT 文件内容（字符串）
        filename: 原始文件名（用于提取客户名称提示）
        my_name_hint: 我方账号名称（帮助区分角色，可选）
        phone: 客户电话（可选，从文件名提取）

    Returns:
        分析结果 dict，包含 Gemini 提取的所有字段 + 解析元数据
    """
    # 从文件名中提取电话号码（如果有）
    if not phone:
        phone_match = re.search(r'\+?\d{7,15}', filename)
        if phone_match:
            phone = phone_match.group(0)

    # 从文件内容中提取电话号码（WhatsApp 表单格式：phone: +993xxxxxxx）
    if not phone:
        content_phone_match = re.search(r'(?:phone|tel|手机|电话)[:\s]*(\+?\d[\d\s\-]{6,17})', chat_text, re.IGNORECASE)
        if content_phone_match:
            phone = re.sub(r'[\s\-]', '', content_phone_match.group(1)).strip()

    # Step 1: 解析 TXT
    parsed = parse_whatsapp_export(chat_text, my_name_hint=my_name_hint)

    if parsed.get("error") or not parsed["messages"]:
        return {
            "success": False,
            "error": parsed.get("error", "对话为空"),
            "filename": filename,
        }

    # Step 2: 格式化对话
    conv_text = _format_conversation_for_gemini(parsed)

    if not conv_text.strip():
        return {
            "success": False,
            "error": "对话内容为空（可能全是媒体文件，无文本消息）",
            "filename": filename,
        }

    # Step 3: Gemini 分析
    customer_name = parsed["customer_name"]
    gemini_result = _call_gemini_for_analysis(conv_text, customer_name)

    if gemini_result.get("error"):
        return {
            "success": False,
            "error": gemini_result["error"],
            "filename": filename,
            "parsed_customer_name": customer_name,
            "message_count": parsed["raw_count"],
        }

    # Step 4: 合并结果
    result = {
        "success": True,
        "id": f"react_{int(time.time())}_{abs(hash(filename)) % 10000:04d}",
        "filename": filename,
        "phone": phone,
        "message_count": parsed["raw_count"],
        "participants": parsed["participants"],
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",  # pending → confirmed → sent
        # Gemini 提取字段
        "customer_name": gemini_result.get("customer_name", customer_name),
        "country": gemini_result.get("country", ""),
        "car_models_interested": gemini_result.get("car_models_interested", []),
        "intent_level": gemini_result.get("intent_level", "unknown"),
        "intent_reason": gemini_result.get("intent_reason", ""),
        "no_deal_reason": gemini_result.get("no_deal_reason", ""),
        "last_contact_summary": gemini_result.get("last_contact_summary", ""),
        "reactivation_message": gemini_result.get("reactivation_message", ""),
        # 原始对话消息（用于前端展示历史聊天记录）
        "messages": [
            {"role": m.get("role", ""), "text": m.get("text", ""), "time": m.get("time", "")}
            for m in parsed.get("messages", [])
        ],
    }

    return result


def analyze_multiple_chats(
    files: List[Dict[str, str]],
    my_name_hint: str = "",
) -> Dict[str, Any]:
    """
    批量分析多个聊天文件（单文件包含一个对话的情况）。

    Args:
        files: [{"filename": "...", "content": "...", "phone": "..."}, ...]
        my_name_hint: 我方名称

    Returns:
        {"success": True, "results": [...], "total": N, "analyzed": M}
    """
    results = []
    errors = []

    for f in files:
        filename = f.get("filename", "unknown.txt")
        content = f.get("content", "")
        phone = f.get("phone", "")

        if not content.strip():
            errors.append({"filename": filename, "error": "文件内容为空"})
            continue

        result = analyze_chat_file(
            chat_text=content,
            filename=filename,
            my_name_hint=my_name_hint,
            phone=phone,
        )
        if result["success"]:
            results.append(result)
        else:
            errors.append({"filename": filename, "error": result.get("error", "未知错误")})

        # 避免 Gemini 限速（Flash 模型有 RPM 限制）
        if len(files) > 1:
            time.sleep(1)

    return {
        "success": True,
        "results": results,
        "errors": errors,
        "total": len(files),
        "analyzed": len(results),
    }


# ─────────────────────────────────────────
# 4. 持久化存储
# ─────────────────────────────────────────

RESULTS_PATH = REACTIVATION_DIR / "reactivation_results.json"


def save_results(results: List[Dict]) -> None:
    REACTIVATION_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_results()
    # 去重（按 id）
    existing_ids = {r["id"] for r in existing}
    new_entries = [r for r in results if r.get("id") not in existing_ids]
    all_results = new_entries + existing  # 新的排在前面
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)


def load_results() -> List[Dict]:
    if not RESULTS_PATH.exists():
        return []
    try:
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def update_result_status(result_id: str, status: str) -> bool:
    """更新单条结果的状态（pending → confirmed → sent）"""
    results = load_results()
    for r in results:
        if r.get("id") == result_id:
            r["status"] = status
            r["status_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    else:
        return False
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return True
