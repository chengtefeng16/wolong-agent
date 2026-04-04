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

RUNTIME_VIEWS = PROJECT_ROOT / "qianqiu_os" / "runtime_views"
H5_VIEWS = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "views"
SESSIONS_DIR = PROJECT_ROOT / "qianqiu_os" / "runtime_sessions" / "whatsapp"
INDEX_PATH = SESSIONS_DIR / "conversation_index.json"
CONVERSATIONS_DIR = SESSIONS_DIR / "conversations"


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
    把测试消息写入 runtime_sessions，然后触发 H5 sync 生成器。
    这模拟了真实 WhatsApp 消息进入系统的流程。
    """
    phone = body.get("phone", "+0000000000")
    name = body.get("name", "测试客户")
    message_text = body.get("message", "")
    country = body.get("country", "未知")

    if not message_text:
        return {"success": False, "error": "message 不能为空"}

    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 写入/更新 conversation 文件
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    safe_phone = phone.replace("+", "").replace(" ", "_")
    conv_path = CONVERSATIONS_DIR / f"{safe_phone}.json"

    existing_conv = _read_json(conv_path, {})
    messages = existing_conv.get("messages", [])
    messages.append({
        "role": "customer",
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

    return {
        "success": True,
        "phone": phone,
        "message": message_text,
        "written_at": now,
        "note": "消息已写入 runtime_sessions，H5 将在下次轮询时更新",
    }


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
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
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

            for msg in messages:
                msg_type = msg.get("type", "")
                wa_id = msg.get("from", "")
                phone = f"+{wa_id}" if not wa_id.startswith("+") else wa_id
                customer_name = contact_map.get(wa_id, "客户")

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
                    # 非文本消息，记录类型但跳过
                    print(f"[Webhook] 跳过非文本消息类型: {msg_type} from {phone}")
                    continue

                if not message_text:
                    continue

                print(f"[Webhook] 收到消息 from {phone} ({customer_name}): {message_text[:60]}")

                result = handle_send_message({
                    "phone": phone,
                    "name": customer_name,
                    "message": message_text,
                    "country": "",  # WhatsApp 不直接提供国家，可通过号码前缀推断
                })

                if result.get("success"):
                    processed.append({"phone": phone, "message": message_text[:60]})
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
            self._send_json(data)

        else:
            self._send_json({"error": f"未知路径: {path}"}, 404)

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

        else:
            self._send_json({"error": f"未知路径: {path}"}, 404)


def main():
    port = 8765
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--port" and sys.argv.index(arg) + 1 < len(sys.argv):
            port = int(sys.argv[sys.argv.index(arg) + 1])

    server = HTTPServer(("0.0.0.0", port), WolongAPIHandler)
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
