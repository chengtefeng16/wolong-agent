# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================
"""
卧龙 Agent 后端 API 服务器 V1
用 Python 标准库 http.server 实现，无需额外依赖。

提供以下 API 端点：
  GET  /api/status          - 系统状态
  POST /api/send_message    - 发送测试消息（触发 AgentOS 处理）
  POST /api/sync            - 手动触发 runtime 数据同步到 H5
  GET  /api/customers       - 返回 WhatsApp 客户列表（直接读 runtime view）

启动方式：
  python3 scripts/api_server.py
  python3 scripts/api_server.py --port 8765

H5 前端通过 Vite proxy 转发到本服务（需配置 vite.config.js）
或者直接用 fetch('http://localhost:8765/api/...') 调用。

用法示例（curl）：
  curl http://localhost:8765/api/status
  curl -X POST http://localhost:8765/api/sync
  curl -X POST http://localhost:8765/api/send_message \\
       -H 'Content-Type: application/json' \\
       -d '{"phone":"+1234567890","name":"Test User","message":"I need 5 SUVs for export"}'
"""

from __future__ import annotations

import json
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import os

# ── 自动加载 .env 文件（优先级低于已有环境变量）──
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:   # 环境变量优先
                    os.environ[_key] = _val

# ── WhatsApp Cloud API 配置（全部走环境变量，不写死）──
WHATSAPP_VERIFY_TOKEN   = os.getenv("WHATSAPP_VERIFY_TOKEN",   "wolong_webhook_token")
WHATSAPP_ACCESS_TOKEN   = os.getenv("WHATSAPP_ACCESS_TOKEN",   "")   # 有值 → 真实发送；空 → dry_run
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1116512831537320")
WHATSAPP_API_VERSION    = os.getenv("WHATSAPP_API_VERSION",    "v19.0")
WA_MODE = "real" if WHATSAPP_ACCESS_TOKEN else "mock"          # 显示在 /api/status

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入同步工具
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    from sync_runtime_to_h5 import sync_once
    SYNC_AVAILABLE = True
except Exception:
    SYNC_AVAILABLE = False

# 导入闭环管理器
try:
    from qianqiu_os.services.closed_loop_manager_v1 import get_closed_loop_manager
    CLOSED_LOOP_AVAILABLE = True
except Exception as _e:
    CLOSED_LOOP_AVAILABLE = False
    print(f"[API] 闭环管理器加载失败: {_e}")

# 导入经验库
try:
    from qianqiu_os.services.experience_store_v1 import get_summary, get_recent_entries, mark_outcome
    EXP_AVAILABLE = True
except Exception:
    EXP_AVAILABLE = False

# 导入历史客户重新激活分析器
try:
    from qianqiu_os.services.reactivation_analyzer_v1 import (
        analyze_chat_file, analyze_multiple_chats,
        save_results, load_results, update_result_status,
    )
    REACTIVATION_AVAILABLE = True
except Exception as _e:
    REACTIVATION_AVAILABLE = False
    print(f"[API] 重新激活分析器加载失败: {_e}")

# ── 数据根目录（Railway 用 DATA_ROOT 指向挂载 Volume）──
_DATA_ROOT = Path(os.getenv("DATA_ROOT", str(PROJECT_ROOT)))

RUNTIME_VIEWS = _DATA_ROOT / "qianqiu_os" / "runtime_views"
H5_VIEWS = _DATA_ROOT / "wolong_h5_console" / "public" / "runtime" / "views"
SESSIONS_DIR = _DATA_ROOT / "qianqiu_os" / "runtime_sessions" / "whatsapp"
INDEX_PATH = SESSIONS_DIR / "conversation_index.json"
CONVERSATIONS_DIR = SESSIONS_DIR / "conversations"

# ── H5 静态文件目录（Railway 用 Vite build 后的 dist/）──
H5_DIST = PROJECT_ROOT / "wolong_h5_console" / "dist"
H5_PUBLIC = PROJECT_ROOT / "wolong_h5_console" / "public"
# /runtime/* 静态数据目录（实时写入，优先从 runtime_views 读）
RUNTIME_ALERTS = _DATA_ROOT / "qianqiu_os" / "runtime_alerts"
RUNTIME_I18N = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "i18n"


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def handle_send_message(body: dict) -> dict:
    """
    把消息写入 runtime_sessions，然后触发 H5 sync 生成器。
    role='agent'  → 我方回复：先真实发 WhatsApp，再存入对话记录
    role='customer'（默认）→ 模拟入站消息，写入对话记录
    """
    phone = body.get("phone", "+0000000000")
    name = body.get("name", "测试客户")
    message_text = body.get("message", "")
    country = body.get("country", "未知")
    role = body.get("role", "customer")   # 'agent' or 'customer'

    if not message_text:
        return {"success": False, "error": "message 不能为空"}

    # ── 若为我方回复，先真实发送 WhatsApp ──
    wa_result = {}
    if role == "agent":
        wa_result = wa_send_message(phone, message_text)
        if not wa_result.get("sent") and wa_result.get("mode") != "dry_run":
            # 发送失败时仍继续写入本地记录，但在返回值里标记
            pass

    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 写入/更新 conversation 文件
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    safe_phone = phone.replace("+", "").replace(" ", "_")
    conv_path = CONVERSATIONS_DIR / f"{safe_phone}.json"

    existing_conv = _read_json(conv_path, {})
    messages = existing_conv.get("messages", [])
    messages.append({
        "role": role,        # 保留真实 role（agent / customer）
        "text": message_text,
        "time": now,
        "timestamp": now,
    })

    conv_data = {
        "phone": phone,
        "customer_name": name,
        "country": country,
        "channel": "whatsapp",
        "bucket": existing_conv.get("bucket", "待判断"),
        "summary": existing_conv.get("summary", message_text[:80]),
        "crm_status": existing_conv.get("crm_status", "unknown"),
        "messages": messages,
        "last_updated": now,
    }
    _write_json(conv_path, conv_data)

    # 2. 更新 conversation_index
    index_data = _read_json(INDEX_PATH, {"index_name": "whatsapp_conversation_index", "items": []})
    items = index_data.get("items", [])
    existing_idx = next((i for i, x in enumerate(items) if x.get("phone") == phone), -1)
    entry = {
        "phone": phone,
        "customer_name": name,
        "country": country,
        "channel": "whatsapp",
        "bucket": existing_conv.get("bucket", "待判断"),
        "latest_message": message_text,
        "last_message_time": now,
        "needs_human_review": False,
        "crm_status": "unknown",
    }
    if existing_idx >= 0:
        items[existing_idx] = entry
    else:
        items.insert(0, entry)
    index_data["items"] = items
    _write_json(INDEX_PATH, index_data)

    # 3. 重新生成 h5_dashboard_whatsapp.json 并同步到 H5
    try:
        from qianqiu_os.services.runtime_whatsapp_h5_sync_v1 import sync
        sync()
    except Exception as e:
        print(f"[API] dashboard 生成失败: {e}")

    # 4. 强制同步到 H5 public 目录
    if SYNC_AVAILABLE:
        sync_once()

    result = {
        "success": True,
        "phone": phone,
        "message": message_text,
        "role": role,
        "written_at": now,
        "note": "消息已写入 runtime_sessions，H5 将在下次轮询时更新",
    }
    if role == "agent":
        result["wa_send"] = wa_result
    return result


def handle_ai_reply(body: dict) -> dict:
    """
    AI 建议回复生成（走闭环管理器 + LLM 网关 + 经验库）。
    有 ANTHROPIC_API_KEY → 真实 Claude 推理
    无 key → 规则模板兜底
    两种情况都会注入历史成功经验提升质量。
    """
    phone = body.get("phone", "")
    customer_name = body.get("customer_name", "客户")
    country = body.get("country", "")
    category = body.get("category", "待判断")
    last_message = body.get("last_message", "").strip()
    conversation_history = body.get("conversation_history", [])
    auto_send = body.get("auto_send", False)

    if not last_message:
        return {"success": False, "error": "last_message 不能为空", "suggested_reply": None}

    if CLOSED_LOOP_AVAILABLE:
        mgr = get_closed_loop_manager()
        result = mgr.process_incoming_message(
            phone=phone,
            customer_name=customer_name,
            country=country,
            message_text=last_message,
            conversation_history=conversation_history,
            existing_category=category,
        )
        return {
            "success": True,
            "task_id": result.get("task_id"),
            "suggested_reply": result.get("suggested_reply", ""),
            "category": result.get("category", category),
            "generated_by": result.get("llm_source", "unknown"),
            "experience_count": result.get("experience_count", 0),
            "auto_send": auto_send,
            "note": f"经验库注入 {result.get('experience_count', 0)} 条历史成功案例",
        }
    else:
        # 降级：直接用 llm_gateway（如可用）或规则
        try:
            from qianqiu_os.services.llm_gateway_v1 import generate_reply
            r = generate_reply(customer_name, country, category, last_message, conversation_history)
            return {
                "success": True,
                "task_id": None,
                "suggested_reply": r.get("suggested_reply", ""),
                "generated_by": r.get("source", "rule_fallback"),
                "experience_count": 0,
                "auto_send": auto_send,
                "note": "闭环管理器未就绪，直接调用 LLM 网关",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "suggested_reply": None}


def handle_approve_reply(body: dict) -> dict:
    """
    人类采纳/修改/拒绝 AI 建议后的回调。
    将决策写入经验库，完成一次闭环。
    """
    task_id = body.get("task_id")
    final_reply = body.get("final_reply", "")
    human_approved = body.get("human_approved", False)
    outcome = body.get("outcome", "unknown")
    quality_score = body.get("quality_score")

    if not task_id:
        return {"success": False, "error": "缺少 task_id"}

    # ── 真实发送（token 有了就自动走真实；否则 dry_run）──
    send_result = {}
    to_phone = body.get("phone", "")
    if human_approved and final_reply and to_phone:
        send_result = wa_send_message(to_phone, final_reply)

    if CLOSED_LOOP_AVAILABLE:
        mgr = get_closed_loop_manager()
        result = mgr.record_human_decision(
            task_id=task_id,
            final_reply=final_reply,
            human_approved=human_approved,
            outcome=outcome,
            quality_score=quality_score,
        )
        return {"success": True, "wa_send": send_result, **result}
    elif EXP_AVAILABLE:
        # 降级：直接存经验
        from qianqiu_os.services.experience_store_v1 import save_experience
        entry_id = save_experience(
            customer_msg=body.get("customer_msg", ""),
            ai_suggested=body.get("ai_suggested", ""),
            final_reply=final_reply,
            human_approved=human_approved,
            category=body.get("category", ""),
            country=body.get("country", ""),
            outcome=outcome,
        )
        return {"success": True, "entry_id": entry_id, "stored": True}
    else:
        return {"success": False, "error": "经验库未就绪"}


def wa_send_message(to_phone: str, text: str) -> dict:
    """
    向客户发送 WhatsApp 消息。
    - WHATSAPP_ACCESS_TOKEN 已配置 → 调用 WhatsApp Cloud API 真实发送
    - 未配置 → dry_run 模式，仅打印日志，不实际发送

    to_phone 格式：+8613122101699 或 8613122101699（自动处理 + 前缀）
    """
    import urllib.request

    phone_digits = to_phone.lstrip("+")

    if not WHATSAPP_ACCESS_TOKEN:
        print(f"[WA][dry_run] 模拟发送给 {to_phone}: {text[:80]}")
        return {"mode": "dry_run", "to": to_phone, "sent": False,
                "note": "设置 WHATSAPP_ACCESS_TOKEN 环境变量后切换为真实发送"}

    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload_bytes = json.dumps({
        "messaging_product": "whatsapp",
        "to": phone_digits,
        "type": "text",
        "text": {"body": text},
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    # 系统代理（HTTP_PROXY）使用自签名证书，Python ssl 默认不信任。
    # 使用 ssl 不验证上下文 + 保持系统代理，与 curl 行为一致。
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
    opener = urllib.request.build_opener(https_handler)
    try:
        with opener.open(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"[WA][real] 已发送给 {to_phone}: {text[:60]} → {result}")
            return {"mode": "real", "to": to_phone, "sent": True, "api_response": result}
    except Exception as e:
        print(f"[WA][real] 发送失败 {to_phone}: {e}")
        return {"mode": "real", "to": to_phone, "sent": False, "error": str(e)}


def handle_mock_incoming(body: dict) -> dict:
    """
    模拟一条入站 WhatsApp 消息（用于测试，不依赖真实 WhatsApp）。
    构造与真实 Webhook 相同的 payload 结构，走同一条处理链路。
    """
    phone = body.get("phone", "+8613122101699")
    name  = body.get("name",  "测试客户")
    text  = body.get("message", "Hello, I want to buy 5 Toyota Corollas.")

    wa_id = phone.lstrip("+")
    fake_webhook = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "818930777978337",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "+8613122101699",
                        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
                    },
                    "contacts": [{"profile": {"name": name}, "wa_id": wa_id}],
                    "messages": [{
                        "from": wa_id,
                        "id": f"mock_{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "text": {"body": text},
                        "type": "text",
                    }],
                },
                "field": "messages",
            }],
        }],
    }
    result = handle_whatsapp_webhook(fake_webhook)
    result["mock"] = True
    return result


def handle_whatsapp_webhook(payload: dict) -> dict:
    """
    解析 WhatsApp Cloud API Webhook 事件，提取消息并写入 runtime_sessions。

    WhatsApp 发来的 payload 结构：
    {
      "object": "whatsapp_business_account",
      "entry": [{
        "changes": [{
          "value": {
            "contacts": [{"profile": {"name": "..."}, "wa_id": "..."}],
            "messages": [{"from": "...", "text": {"body": "..."}, "type": "text", "timestamp": "..."}]
          }
        }]
      }]
    }
    """
    processed = []
    errors = []

    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if value.get("messaging_product") != "whatsapp":
                continue

            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            # 建立 wa_id → 姓名 的映射
            contact_map = {c.get("wa_id", ""): c.get("profile", {}).get("name", "客户") for c in contacts}

            # ── 处理状态回执（已读/已送达），直接跳过 ──
            statuses = value.get("statuses", [])
            if statuses and not messages:
                continue

            for msg in messages:
                msg_type = msg.get("type", "")
                wa_id = msg.get("from", "")
                to_wa_id = msg.get("to", "")  # message_echoes 有 "to" 字段

                # ── 判断是否为 message_echo（我方从手机发出的消息）──
                my_phone_id = WHATSAPP_PHONE_NUMBER_ID  # 我方号码 ID
                is_echo = bool(to_wa_id) and (
                    wa_id == my_phone_id or
                    wa_id.replace("+", "") == my_phone_id
                )

                if is_echo:
                    # Echo：我方发出的消息，to 是客户号码
                    customer_wa_id = to_wa_id.replace("+", "")
                    phone = f"+{customer_wa_id}" if not to_wa_id.startswith("+") else to_wa_id
                    customer_name = contact_map.get(customer_wa_id, "客户")
                    role = "agent"
                    print(f"[Webhook] 📤 手机发出的消息 to {phone}: ", end="")
                else:
                    # 普通入站消息
                    phone = f"+{wa_id}" if not wa_id.startswith("+") else wa_id
                    customer_name = contact_map.get(wa_id, "客户")
                    role = "customer"

                # 只处理文本消息（后续可扩展图片/语音等）
                if msg_type == "text":
                    message_text = msg.get("text", {}).get("body", "").strip()
                elif msg_type == "button":
                    message_text = msg.get("button", {}).get("text", "").strip()
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    message_text = (
                        interactive.get("button_reply", {}).get("title", "") or
                        interactive.get("list_reply", {}).get("title", "") or
                        ""
                    ).strip()
                else:
                    print(f"[Webhook] 跳过非文本消息类型: {msg_type} from {phone}")
                    continue

                if not message_text:
                    continue

                if not is_echo:
                    print(f"[Webhook] 📥 收到消息 from {phone} ({customer_name}): {message_text[:60]}")
                else:
                    print(message_text[:60])

                result = handle_send_message({
                    "phone": phone,
                    "name": customer_name,
                    "message": message_text,
                    "role": role,
                    "country": "",
                })

                if result.get("success"):
                    processed.append({"phone": phone, "message": message_text[:60]})
                    # ── 后台自动生成 AI 建议，存入对话 JSON ──
                    def _auto_generate_ai(phone=phone, customer_name=customer_name,
                                          message_text=message_text):
                        try:
                            from qianqiu_os.services.llm_gateway_v1 import generate_reply
                            safe_phone = phone.replace("+", "").replace(" ", "_")
                            conv_path = CONVERSATIONS_DIR / f"{safe_phone}.json"
                            conv = _read_json(conv_path, {})
                            history = conv.get("messages", [])
                            country = conv.get("country", "")
                            category = conv.get("bucket", "疑似车商")
                            r = generate_reply(customer_name, country, category,
                                               message_text, history)
                            if r.get("suggested_reply"):
                                conv["pending_ai_reply"] = {
                                    "text": r["suggested_reply"],
                                    "source": r.get("source", "unknown"),
                                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                }
                                _write_json(conv_path, conv)
                                print(f"[AI-Auto] 已为 {phone} 预生成建议回复 ({r.get('source')})")
                        except Exception as e:
                            print(f"[AI-Auto] 预生成失败 {phone}: {e}")
                    import threading
                    threading.Thread(target=_auto_generate_ai, daemon=True).start()
                else:
                    errors.append({"phone": phone, "error": result.get("error", "unknown")})

    return {
        "success": True,
        "processed": len(processed),
        "errors": len(errors),
        "details": processed,
    }


def handle_reflection(body: dict) -> dict:
    """触发反思周期，分析近期经验，提炼改进洞察"""
    recent_n = body.get("recent_n", 20)

    if CLOSED_LOOP_AVAILABLE:
        mgr = get_closed_loop_manager()
        return mgr.run_reflection_cycle(recent_n=recent_n)
    else:
        return {"status": "unavailable", "error": "闭环管理器未就绪"}


def handle_translate(body: dict) -> dict:
    """批量翻译文本为中文，使用 Gemini API"""
    import urllib.request
    import ssl
    import time as _time
    import re

    texts = body.get("texts", [])
    if not texts:
        return {"translations": []}

    # 加载 API key（复用 reactivation 的方式）
    try:
        from qianqiu_os.services.reactivation_analyzer_v1 import _load_gemini_key
        api_key = _load_gemini_key()
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"error": "GEMINI_API_KEY 未配置", "translations": texts}

    # 构建批量翻译 prompt
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        "将以下每条文本翻译成中文。保持原意和语气。"
        "严格按格式输出：每行一条，格式为「序号. 中文翻译」，不要任何额外说明。\n\n"
        + numbered
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.1},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    proxies = {
        "https": os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", "")),
        "http":  os.environ.get("HTTP_PROXY",  os.environ.get("http_proxy",  "")),
    }
    proxy_handler = urllib.request.ProxyHandler({k: v for k, v in proxies.items() if v})
    opener = urllib.request.build_opener(proxy_handler,
                                          urllib.request.HTTPSHandler(context=ssl_ctx))
    last_error = ""
    for attempt in range(3):
        if attempt > 0:
            _time.sleep(3 * attempt)
        try:
            with opener.open(req, timeout=30) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text_out = (
                    raw.get("candidates", [{}])[0]
                       .get("content", {})
                       .get("parts", [{}])[0]
                       .get("text", "")
                )
                # 解析 "1. 翻译\n2. 翻译\n..." 格式
                translations = []
                for line in text_out.strip().splitlines():
                    m = re.match(r"^\d+\.\s*(.+)$", line.strip())
                    if m:
                        translations.append(m.group(1).strip())
                # 数量对齐（Gemini 偶尔漏行）
                while len(translations) < len(texts):
                    translations.append("")
                return {"translations": translations[:len(texts)]}
        except Exception as e:
            last_error = str(e)
            if "503" in last_error or "429" in last_error or "400" in last_error:
                continue
            return {"error": str(e), "translations": texts}
    return {"error": f"翻译重试失败: {last_error}", "translations": texts}


def handle_reactivation_analyze(body: dict) -> dict:
    if not REACTIVATION_AVAILABLE:
        return {"success": False, "error": "重新激活分析器未就绪"}
    my_name_hint = body.get("my_name_hint", "")
    if "files" in body:
        files = body["files"]
    elif "content" in body:
        files = [{"filename": body.get("filename", "chat.txt"), "content": body["content"], "phone": body.get("phone", "")}]
    else:
        return {"success": False, "error": "缺少 content 或 files 字段"}
    result = analyze_multiple_chats(files, my_name_hint=my_name_hint)
    if result.get("results"):
        save_results(result["results"])
    return result


def handle_reactivation_list(params: dict) -> dict:
    if not REACTIVATION_AVAILABLE:
        return {"success": False, "error": "重新激活分析器未就绪"}
    results = load_results()
    status_filter = params.get("status", "")
    if status_filter:
        results = [r for r in results if r.get("status") == status_filter]
    return {"success": True, "results": results, "total": len(results)}


def handle_reactivation_update_status(body: dict) -> dict:
    if not REACTIVATION_AVAILABLE:
        return {"success": False, "error": "重新激活分析器未就绪"}
    result_id = body.get("id")
    new_status = body.get("status")
    if not result_id or not new_status:
        return {"success": False, "error": "缺少 id 或 status 字段"}
    ok = update_result_status(result_id, new_status)
    return {"success": ok, "id": result_id, "status": new_status}


USERS_FILE = PROJECT_ROOT / "qianqiu_os" / "data" / "users.json"
CUSTOMER_TAGS_FILE = PROJECT_ROOT / "qianqiu_os" / "data" / "customer_tags.json"

# ── 客户标签 & 备注 ──
def _load_customer_tags() -> dict:
    if not CUSTOMER_TAGS_FILE.exists():
        return {}
    try:
        return json.loads(CUSTOMER_TAGS_FILE.read_text("utf-8"))
    except Exception:
        return {}

def _save_customer_tags(data: dict):
    CUSTOMER_TAGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def handle_get_customer_meta(params: dict) -> dict:
    phone = params.get("phone", "")
    if not phone:
        return {"error": "phone required"}
    db = _load_customer_tags()
    entry = db.get(phone, {"tags": [], "notes": ""})
    return {"phone": phone, "tags": entry.get("tags", []), "notes": entry.get("notes", "")}

def handle_get_all_customer_meta() -> dict:
    return _load_customer_tags()

def handle_save_customer_meta(body: dict) -> dict:
    phone = str(body.get("phone", "")).strip()
    if not phone:
        return {"success": False, "error": "phone required"}
    tags = [str(t) for t in body.get("tags", []) if t]
    notes = str(body.get("notes", ""))
    biz_type = str(body.get("bizType", ""))
    db = _load_customer_tags()
    db[phone] = {"tags": tags, "notes": notes, "bizType": biz_type, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    _save_customer_tags(db)
    return {"success": True}

def _load_users() -> list:
    if not USERS_FILE.exists():
        return []
    try:
        return json.loads(USERS_FILE.read_text("utf-8")).get("users", [])
    except Exception:
        return []

def handle_login(body: dict) -> dict:
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", "")).strip()
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
    for user in _load_users():
        if user.get("username") == username and user.get("password") == password:
            return {
                "success": True,
                "user": {
                    "username": user["username"],
                    "display_name": user.get("display_name", username),
                    "role": user.get("role", "sales"),
                    "assigned_phones": user.get("assigned_phones", []),
                },
            }
    return {"success": False, "error": "用户名或密码错误"}

def handle_get_users(params: dict) -> dict:
    users = [
        {"username": u["username"], "display_name": u.get("display_name", u["username"]), "role": u.get("role", "sales")}
        for u in _load_users()
    ]
    return {"users": users}


# ── 消息模板管理 ──
TEMPLATES_FILE = PROJECT_ROOT / "qianqiu_os" / "data" / "message_templates.json"

PRESET_TEMPLATES = [
    {
        "id": "tpl_trade_en",
        "name": "贸易-英文开场",
        "bizType": "trade",
        "lang": "en",
        "langLabel": "英文",
        "content": "Hi {name}, I'm from KunYueTong Auto Export. We specialize in used vehicle exports to {country}. Would you be interested in our competitive prices and reliable service?",
    },
    {
        "id": "tpl_trade_ru",
        "name": "贸易-俄文开场",
        "bizType": "trade",
        "lang": "ru",
        "langLabel": "俄文",
        "content": "Здравствуйте, {name}! Я представляю компанию по экспорту подержанных автомобилей из Китая. Нас интересует сотрудничество с {country}. Готовы обсудить?",
    },
    {
        "id": "tpl_saas_zh",
        "name": "SaaS-中文开场",
        "bizType": "saas",
        "lang": "zh",
        "langLabel": "中文",
        "content": "您好{name}，我们是cncar国家政策法规查询系统，专为国际贸易商提供各国进口政策、关税、法规的一站式查询服务。是否方便了解一下？",
    },
]

def _load_templates() -> list:
    if not TEMPLATES_FILE.exists():
        _save_templates(PRESET_TEMPLATES)
        return list(PRESET_TEMPLATES)
    try:
        data = json.loads(TEMPLATES_FILE.read_text("utf-8"))
        return data if isinstance(data, list) else PRESET_TEMPLATES
    except Exception:
        return list(PRESET_TEMPLATES)

def _save_templates(data: list):
    TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def handle_get_templates() -> list:
    return _load_templates()

def handle_save_template(body: dict) -> dict:
    """新增或更新一个模板（body 即完整模板对象，需有 id）"""
    tpl_id = str(body.get("id", "")).strip()
    if not tpl_id:
        return {"success": False, "error": "id 不能为空"}
    templates = _load_templates()
    idx = next((i for i, t in enumerate(templates) if t.get("id") == tpl_id), -1)
    if idx >= 0:
        templates[idx] = body
    else:
        templates.append(body)
    _save_templates(templates)
    return {"success": True, "templates": templates}

def handle_delete_template(tpl_id: str) -> dict:
    templates = _load_templates()
    templates = [t for t in templates if t.get("id") != tpl_id]
    _save_templates(templates)
    return {"success": True, "templates": templates}


# ── 新建联系（主动发起 WhatsApp）──
NEW_CONTACTS_FILE = PROJECT_ROOT / "qianqiu_os" / "data" / "new_contacts.json"

def _load_new_contacts() -> list:
    if not NEW_CONTACTS_FILE.exists():
        return []
    try:
        return json.loads(NEW_CONTACTS_FILE.read_text("utf-8"))
    except Exception:
        return []

def _save_new_contacts(data: list):
    NEW_CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    NEW_CONTACTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def handle_new_contact(body: dict) -> dict:
    phone = str(body.get("phone", "")).strip()
    name = str(body.get("name", "")).strip() or phone
    country = str(body.get("country", "")).strip()
    message = str(body.get("message", "")).strip()

    if not phone:
        return {"success": False, "error": "手机号不能为空"}
    if not message:
        return {"success": False, "error": "消息内容不能为空"}

    # 标准化手机号（确保有 + 前缀）
    if not phone.startswith("+"):
        phone = "+" + phone

    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    contact = {
        "phone": phone,
        "name": name,
        "country": country,
        "first_message": message,
        "created_at": ts,
    }

    # 持久化到 new_contacts.json
    contacts = _load_new_contacts()
    updated = False
    for i, c in enumerate(contacts):
        if c.get("phone") == phone:
            contacts[i] = contact
            updated = True
            break
    if not updated:
        contacts.append(contact)
    _save_new_contacts(contacts)

    # 若有真实 Token，尝试调用 WhatsApp API（普通文本消息）
    # ⚠️  主动发起需要模板消息，此处仅做 dry_run 或 real 记录
    if WHATSAPP_ACCESS_TOKEN:
        wa_result = wa_send_message(phone, message)
        sent = wa_result.get("sent", False)
        print(f"[new_contact][real] {name}({phone}) → sent={sent}")
        return {
            "success": True,
            "mode": "real",
            "contact": contact,
            "wa_result": wa_result,
            "note": "已调用 WhatsApp API（主动发起需审批模板消息才能到达新用户）",
        }
    else:
        print(f"[new_contact][mock] 模拟新建联系 {name}({phone}): {message[:60]}")
        return {
            "success": True,
            "mode": "mock",
            "contact": contact,
            "note": "测试模式：联系人已保存到本地，未发送真实消息。配置 WHATSAPP_ACCESS_TOKEN 后切换为真实发送。",
        }


class WolongAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 简化日志
        print(f"[API] {self.address_string()} {format % args}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_plain(self, text: str, status: int = 200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, file_path: Path, content_type: str = None):
        """服务静态文件（用于 H5 dist/ 和 /runtime/* 数据文件）"""
        if not file_path.exists():
            self._send_json({"error": "Not found"}, 404)
            return
        import mimetypes
        if content_type is None:
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"
        with open(file_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # ── WhatsApp Webhook 验证（Meta 平台要求）──
        if path == "/webhook":
            params = parse_qs(parsed.query)
            mode = params.get("hub.mode", [""])[0]
            token = params.get("hub.verify_token", [""])[0]
            challenge = params.get("hub.challenge", [""])[0]

            if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
                print(f"[Webhook] WhatsApp 验证成功，返回 challenge: {challenge}")
                self._send_plain(challenge, 200)
            else:
                print(f"[Webhook] 验证失败: mode={mode}, token={token}")
                self._send_plain("Verification failed", 403)
            return

        if path == "/api/status":
            loop_status = {}
            if CLOSED_LOOP_AVAILABLE:
                try:
                    mgr = get_closed_loop_manager()
                    loop_status = mgr.get_loop_status()
                except Exception:
                    pass
            self._send_json({
                "status": "ok",
                "project": "AgentOS / Wolong Agent",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "sync_available": SYNC_AVAILABLE,
                "closed_loop": loop_status,
                "wa_mode": WA_MODE,
                "wa_phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
            })

        elif path == "/api/experience/summary":
            if EXP_AVAILABLE:
                from qianqiu_os.services.experience_store_v1 import get_summary
                self._send_json(get_summary())
            else:
                self._send_json({"error": "经验库未就绪"}, 503)

        elif path == "/api/experience/recent":
            if EXP_AVAILABLE:
                from qianqiu_os.services.experience_store_v1 import get_recent_entries
                self._send_json({"entries": get_recent_entries(10)})
            else:
                self._send_json({"error": "经验库未就绪"}, 503)

        elif path == "/api/customers":
            data = _read_json(
                H5_VIEWS / "h5_dashboard_whatsapp.json",
                {"customers": [], "dashboard_name": "h5_dashboard_whatsapp"}
            )
            # 合并 new_contacts.json 中主动创建的联系人（置顶显示）
            new_contacts = _load_new_contacts()
            if new_contacts:
                existing_phones = {c.get("phone") or c.get("id") for c in data.get("customers", [])}
                extra = []
                for nc in reversed(new_contacts):  # 最新的排最前
                    phone = nc.get("phone", "")
                    if phone not in existing_phones:
                        extra.append({
                            "id": phone,
                            "phone": phone,
                            "name": nc.get("name") or phone,
                            "category": "新建联系",
                            "country": nc.get("country", ""),
                            "channel": "whatsapp",
                            "time": nc.get("created_at", ""),
                            "message": nc.get("first_message", ""),
                            "messages": [
                                {"role": "agent", "text": nc.get("first_message", ""), "time": nc.get("created_at", "")}
                            ],
                            "_isNewContact": True,
                        })
                if extra:
                    data = dict(data)
                    data["customers"] = extra + list(data.get("customers", []))
            self._send_json(data)

        elif path == "/api/reactivation/list":
            flat_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            self._send_json(handle_reactivation_list(flat_params))

        # ── /runtime/* 动态数据文件（H5 轮询用）──
        elif path.startswith("/runtime/"):
            rel = path[len("/runtime/"):]  # e.g. "views/h5_dashboard_whatsapp.json"
            # 优先级：1. 实时 runtime_views（webhook 更新后最新）
            #          2. dist/runtime（Railway build 时的快照）
            #          3. public/runtime（git 中的静态文件）
            if rel.startswith("views/"):
                live_candidate = RUNTIME_VIEWS / rel[len("views/"):]
            elif rel.startswith("alerts/"):
                live_candidate = RUNTIME_ALERTS / rel[len("alerts/"):]
            elif rel.startswith("i18n/"):
                live_candidate = RUNTIME_I18N / rel[len("i18n/"):]
            else:
                live_candidate = H5_PUBLIC / "runtime" / rel  # fallback 到 public
            if live_candidate.exists():
                self._serve_static(live_candidate)
            elif (H5_DIST / "runtime" / rel).exists():
                self._serve_static(H5_DIST / "runtime" / rel)
            elif (H5_PUBLIC / "runtime" / rel).exists():
                self._serve_static(H5_PUBLIC / "runtime" / rel)
            else:
                self._send_json({"error": f"runtime file not found: {rel}"}, 404)

        elif path == "/api/users":
            self._send_json(handle_get_users(flat_params))

        elif path == "/api/customer_meta":
            self._send_json(handle_get_customer_meta(flat_params))

        elif path == "/api/customer_meta_all":
            self._send_json(handle_get_all_customer_meta())

        elif path == "/api/templates":
            self._send_json(handle_get_templates())

        # ── H5 静态文件（Railway 生产模式：从 dist/ 服务）──
        elif H5_DIST.exists() and not path.startswith("/api/"):
            # 生产模式：从 Vite build 产物服务
            if path == "/" or path == "":
                self._serve_static(H5_DIST / "index.html", "text/html; charset=utf-8")
            else:
                static_file = H5_DIST / path.lstrip("/")
                if static_file.exists() and static_file.is_file():
                    self._serve_static(static_file)
                else:
                    # SPA fallback：所有未知路由都返回 index.html
                    self._serve_static(H5_DIST / "index.html", "text/html; charset=utf-8")

        else:
            self._send_json({"error": f"未知路径: {path}"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        flat_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if path == "/api/templates":
            tpl_id = flat_params.get("id", "")
            result = handle_delete_template(tpl_id)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.wfile.write(json.dumps({"error": f"DELETE 未知路径: {path}"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            body = {}

        # ── WhatsApp Webhook 消息接收 ──
        if path == "/webhook":
            print(f"[Webhook-RAW] {str(body)[:500]}")
            result = handle_whatsapp_webhook(body)
            self._send_json(result)
            # 收到消息后自动同步到 H5（两步：重建视图 + 拷贝到 public）
            if result.get("processed", 0) > 0:
                try:
                    from qianqiu_os.services.runtime_whatsapp_h5_sync_v1 import sync as rebuild_dashboard
                    rebuild_dashboard()
                except Exception as e:
                    print(f"[webhook] dashboard重建失败: {e}")
                if SYNC_AVAILABLE:
                    try:
                        sync_once()
                    except Exception as e:
                        print(f"[webhook] 文件同步失败: {e}")
            return

        if path == "/api/sync":
            if SYNC_AVAILABLE:
                result = sync_once()
                self._send_json({"success": True, "result": result})
            else:
                self._send_json({"success": False, "error": "sync 模块未加载"}, 500)

        elif path == "/api/send_message":
            result = handle_send_message(body)
            self._send_json(result)

        elif path == "/api/ai_reply":
            result = handle_ai_reply(body)
            self._send_json(result)

        elif path == "/api/approve_reply":
            result = handle_approve_reply(body)
            self._send_json(result)

        elif path == "/api/reflection":
            result = handle_reflection(body)
            self._send_json(result)

        elif path == "/api/mock_incoming":
            # 模拟一条入站 WhatsApp 消息（不依赖真实 WhatsApp，走完整处理链路）
            result = handle_mock_incoming(body)
            self._send_json(result)

        elif path == "/api/reactivation/analyze":
            result = handle_reactivation_analyze(body)
            self._send_json(result)

        elif path == "/api/reactivation/update_status":
            result = handle_reactivation_update_status(body)
            self._send_json(result)

        elif path == "/api/translate":
            result = handle_translate(body)
            self._send_json(result)

        elif path == "/api/login":
            result = handle_login(body)
            self._send_json(result)

        elif path == "/api/customer_meta":
            result = handle_save_customer_meta(body)
            self._send_json(result)

        elif path == "/api/new_contact":
            result = handle_new_contact(body)
            self._send_json(result)

        elif path == "/api/templates":
            result = handle_save_template(body)
            self._send_json(result)

        else:
            self._send_json({"error": f"POST 未知路径: {path}"}, 404)


def main():
    # Railway 通过 $PORT 注入端口；命令行参数次之；默认 8765
    port = int(os.getenv("PORT", 8765))
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--port" and sys.argv.index(arg) + 1 < len(sys.argv):
            port = int(sys.argv[sys.argv.index(arg) + 1])

    server = HTTPServer(("0.0.0.0", port), WolongAPIHandler)
    # ── 启动时自动激活 WABA 订阅 ──
    def _activate_waba():
        import urllib.request, urllib.error, ssl, json as _json
        waba_id = "2817262535309287"
        token = WHATSAPP_ACCESS_TOKEN
        if not token:
            print("[WABA] ⚠️  未配置 WHATSAPP_ACCESS_TOKEN，跳过订阅激活")
            return
        try:
            url = f"https://graph.facebook.com/v20.0/{waba_id}/subscribed_apps"
            req = urllib.request.Request(url, method="POST")
            req.add_header("Authorization", f"Bearer {token}")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                result = _json.loads(resp.read())
                if result.get("success"):
                    print("[WABA] ✅ WABA 订阅已激活")
                else:
                    print(f"[WABA] ⚠️  激活失败: {result}")
            # 查询并打印当前 webhook 配置
            phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1116512831537320")
            check_url = f"https://graph.facebook.com/v19.0/{phone_id}?fields=webhook_configuration&access_token={token}"
            req2 = urllib.request.Request(check_url)
            with urllib.request.urlopen(req2, timeout=15, context=ctx) as resp2:
                wh = _json.loads(resp2.read())
                current = wh.get('webhook_configuration', {}).get('application', '')
                print(f"[WABA] 当前 webhook: {current}")
                railway_url = "https://wolong-agent-production.up.railway.app/webhook"
                if current != railway_url:
                    print(f"[WABA] 尝试更新 webhook 到 Railway...")
                    update_url = f"https://graph.facebook.com/v19.0/{phone_id}"
                    import urllib.parse as _parse
                    data = _parse.urlencode({
                        "webhook_url": railway_url,
                        "access_token": token
                    }).encode()
                    req3 = urllib.request.Request(update_url, data=data, method="POST")
                    req3.add_header("Content-Type", "application/x-www-form-urlencoded")
                    with urllib.request.urlopen(req3, timeout=15, context=ctx) as resp3:
                        update_result = _json.loads(resp3.read())
                        print(f"[WABA] 更新结果: {update_result}")
                    # 验证更新是否生效
                    check2_url = f"https://graph.facebook.com/v19.0/{phone_id}?fields=webhook_configuration&access_token={token}"
                    req4 = urllib.request.Request(check2_url)
                    with urllib.request.urlopen(req4, timeout=15, context=ctx) as resp4:
                        wh2 = _json.loads(resp4.read())
                        print(f"[WABA] 更新后 webhook: {wh2.get('webhook_configuration', {})}")
                else:
                    print(f"[WABA] ✅ webhook 已是 Railway 地址")
        except Exception as e:
            print(f"[WABA] ⚠️  激活异常: {e}")
    import threading as _threading
    _threading.Thread(target=_activate_waba, daemon=True).start()

    print(f"[API] 卧龙 Agent 后端 API 服务器已启动: http://localhost:{port}")
    print(f"[API] WhatsApp 模式: {'🟢 真实发送 (WHATSAPP_ACCESS_TOKEN 已配置)' if WA_MODE == 'real' else '🟡 dry_run/mock (未配置 WHATSAPP_ACCESS_TOKEN)'}")
    print(f"[API] Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    print(f"[API]")
    print(f"[API] 主要接口:")
    print(f"[API]   GET  /api/status              系统状态（含 wa_mode）")
    print(f"[API]   POST /api/mock_incoming        模拟入站消息（Mock 测试用）")
    print(f"[API]   POST /api/ai_reply             获取 AI 建议回复")
    print(f"[API]   POST /api/approve_reply        采纳并发送（dry_run 或真实）")
    print(f"[API] WhatsApp Webhook:")
    print(f"[API]   GET  /webhook                  Meta 验证（verify_token={WHATSAPP_VERIFY_TOKEN}）")
    print(f"[API]   POST /webhook                  接收真实消息")
    print(f"[API]")
    print(f"[API] 切换真实发送:")
    print(f"[API]   export WHATSAPP_ACCESS_TOKEN=<your_token>")
    print(f"[API]   export WHATSAPP_PHONE_NUMBER_ID=1116512831537320")
    print(f"[API]   重启服务器即可")
    print(f"[API]")
    print(f"[API] 按 Ctrl+C 停止...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] 已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()
