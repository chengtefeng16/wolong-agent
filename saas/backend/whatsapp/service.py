"""
WhatsApp 服务层：
- WABA 接入（Embedded Signup code 换凭证 → 加密存储）
- Webhook 路由（phone_number_id → tenant）
- 消息存储 + AI 草稿生成
"""
from __future__ import annotations

import json
import threading
import time
from base64 import b64decode, b64encode
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import AIDraft, Conversation, Message, UsageEvent, WABAAccount
from .bsp.interface import WABACredentials
from .bsp.meta import get_meta_provider


# ── Token encryption ──────────────────────────────────────────────────────────

def _fernet():
    from cryptography.fernet import Fernet
    key = get_settings().token_encryption_key
    if not key:
        # Dev fallback: generate a stable key from JWT secret (NOT for production)
        import hashlib, base64
        raw = get_settings().jwt_secret.encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(key if isinstance(key, bytes) else key.encode())


def encrypt_token(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_token(enc: str) -> str:
    return _fernet().decrypt(enc.encode()).decode()


# ── WABA connection ───────────────────────────────────────────────────────────

async def connect_waba(db: AsyncSession, tenant_id: str, code: str) -> WABAAccount:
    """
    Embedded Signup v4 完成回调：
    1. 用 code 换 WABACredentials
    2. 加密存 token
    3. 订阅 webhook
    4. 存入 waba_accounts 表
    """
    provider = get_meta_provider()
    creds: WABACredentials = await provider.exchange_signup_code(code)

    # 检查是否已存在同一 phone_number_id（不允许同一号码被两个租户连接）
    existing = await db.scalar(
        select(WABAAccount).where(WABAAccount.phone_number_id == creds.phone_number_id)
    )
    if existing and existing.tenant_id != tenant_id:
        raise ValueError("This WhatsApp number is already connected to another account.")

    enc_token = encrypt_token(creds.access_token)

    if existing:
        existing.access_token_enc = enc_token
        existing.waba_id = creds.waba_id
        existing.display_phone = creds.display_phone
        existing.status = "active"
        await db.commit()
        waba = existing
    else:
        waba = WABAAccount(
            tenant_id=tenant_id,
            waba_id=creds.waba_id,
            phone_number_id=creds.phone_number_id,
            display_phone=creds.display_phone,
            access_token_enc=enc_token,
            provider=creds.provider,
        )
        db.add(waba)
        await db.flush()

    # Subscribe webhook
    try:
        ok = await provider.subscribe_webhook(creds.waba_id, creds)
        waba.webhook_subscribed = ok
    except Exception:
        waba.webhook_subscribed = False

    await db.commit()
    await db.refresh(waba)
    return waba


# ── Webhook routing ───────────────────────────────────────────────────────────

async def route_webhook(db: AsyncSession, payload: dict) -> dict:
    """
    入站 webhook payload → 按 phone_number_id 找到对应租户 → 处理消息
    """
    processed = []
    errors = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if value.get("messaging_product") != "whatsapp":
                continue

            # 路由：用 phone_number_id 找 WABAAccount → 得到 tenant_id
            meta = value.get("metadata", {})
            phone_number_id = meta.get("phone_number_id", "")
            waba = await db.scalar(
                select(WABAAccount).where(WABAAccount.phone_number_id == phone_number_id)
            )
            if not waba:
                errors.append({"phone_number_id": phone_number_id, "error": "no_waba_account"})
                continue

            # 处理状态回执，跳过
            if value.get("statuses") and not value.get("messages"):
                continue

            contacts = value.get("messages", [])
            contact_map = {
                c.get("wa_id", ""): c.get("profile", {}).get("name", "")
                for c in value.get("contacts", [])
            }

            for msg in value.get("messages", []):
                try:
                    result = await _handle_inbound_message(db, waba, msg, contact_map)
                    processed.append(result)
                except Exception as e:
                    errors.append({"error": str(e)})

    return {"processed": len(processed), "errors": errors}


async def _handle_inbound_message(
    db: AsyncSession,
    waba: WABAAccount,
    msg: dict,
    contact_map: dict,
) -> dict:
    """存储入站消息，触发后台 AI 草稿生成"""
    msg_type = msg.get("type", "")
    wa_id = msg.get("from", "")    # 客户的 BSUID (wa_id)
    wamid = msg.get("id", "")

    # 提取文本
    if msg_type == "text":
        text = msg.get("text", {}).get("body", "").strip()
    elif msg_type == "button":
        text = msg.get("button", {}).get("text", "").strip()
    elif msg_type == "interactive":
        iv = msg.get("interactive", {})
        text = (iv.get("button_reply", {}).get("title") or iv.get("list_reply", {}).get("title") or "").strip()
    else:
        return {"skipped": msg_type}

    if not text:
        return {"skipped": "empty"}

    customer_name = contact_map.get(wa_id, "")

    # 查找或创建 Conversation
    conv = await db.scalar(
        select(Conversation).where(
            Conversation.waba_id == waba.id,
            Conversation.customer_bsuid == wa_id,
        )
    )
    if not conv:
        conv = Conversation(
            tenant_id=waba.tenant_id,
            waba_id=waba.id,
            customer_bsuid=wa_id,
            customer_name=customer_name or wa_id,
        )
        db.add(conv)
        await db.flush()
    elif customer_name and not conv.customer_name:
        conv.customer_name = customer_name

    # 写入消息
    message = Message(
        conversation_id=conv.id,
        tenant_id=waba.tenant_id,
        role="customer",
        text=text,
        wa_message_id=wamid,
    )
    db.add(message)
    conv.updated_at = datetime.now(timezone.utc)
    conv.status = "open"
    await db.commit()

    # 触发后台 AI 草稿生成（不阻塞 webhook 响应）
    threading.Thread(
        target=_generate_ai_draft_sync,
        args=(conv.id, waba.tenant_id, text, conv.customer_name, conv.country, conv.bucket),
        daemon=True,
    ).start()

    return {"conversation_id": conv.id, "bsuid": wa_id, "text_preview": text[:60]}


# ── AI draft generation (sync wrapper for threading) ─────────────────────────

def _generate_ai_draft_sync(
    conversation_id: str,
    tenant_id: str,
    last_message: str,
    customer_name: str,
    country: str,
    bucket: str,
):
    """在独立线程里调用 AI，写 AIDraft 记录。用 sync DB session。"""
    import asyncio
    from ..database import AsyncSessionLocal
    from ..ai.service import generate_reply

    async def _run():
        async with AsyncSessionLocal() as db:
            # 取最近 5 条历史消息
            msgs = await db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(6)
            )
            history = [
                {"role": m.role, "text": m.text}
                for m in reversed(list(msgs))
                if m.text.strip()
            ]
            history = history[:-1]  # 去掉刚写入的这条（已经是 last_message）

            result = await generate_reply(
                customer_name=customer_name,
                country=country,
                category=bucket,
                last_message=last_message,
                conversation_history=history,
            )
            if not result.get("suggested_reply"):
                return

            draft = AIDraft(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                text=result["suggested_reply"],
                source=result.get("source", "gemini"),
                language_code=result.get("language_code", "en"),
            )
            db.add(draft)

            # 更新 conversation 状态
            conv = await db.get(Conversation, conversation_id)
            if conv:
                conv.has_pending_draft = True

            # 计量
            db.add(UsageEvent(tenant_id=tenant_id, event_type="ai_reply"))
            await db.commit()

    asyncio.run(_run())


# ── Send approved reply ───────────────────────────────────────────────────────

async def send_approved_reply(
    db: AsyncSession,
    draft_id: str,
    tenant_id: str,
    final_text: str | None = None,
) -> dict:
    """人工审批后发送。final_text 非空时用修改后的文本，否则用草稿原文。"""
    draft = await db.get(AIDraft, draft_id)
    if not draft or draft.tenant_id != tenant_id:
        return {"success": False, "error": "Draft not found"}
    if draft.status != "pending":
        return {"success": False, "error": "Already handled"}

    text_to_send = (final_text or draft.text).strip()
    if not text_to_send:
        return {"success": False, "error": "Empty message"}

    # 标记处理中（防双击）
    draft.status = "processing"
    await db.commit()

    conv = await db.get(Conversation, draft.conversation_id)
    waba = await db.get(WABAAccount, conv.waba_id)

    from .bsp.meta import get_meta_provider
    creds = WABACredentials(
        waba_id=waba.waba_id,
        phone_number_id=waba.phone_number_id,
        display_phone=waba.display_phone,
        access_token=decrypt_token(waba.access_token_enc),
    )
    send_result = await get_meta_provider().send_text(conv.customer_bsuid, text_to_send, creds)

    now = datetime.now(timezone.utc)
    if send_result.sent:
        draft.status = "sent"
        draft.resolved_at = now
        msg = Message(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            role="agent",
            text=text_to_send,
            wa_message_id=send_result.wa_message_id,
            status="sent",
        )
        db.add(msg)
        conv.has_pending_draft = False
        conv.status = "replied"
        conv.updated_at = now
        db.add(UsageEvent(tenant_id=tenant_id, event_type="wa_message_sent"))
    else:
        draft.status = "pending"  # 回退可重试
    await db.commit()

    return {
        "success": send_result.sent,
        "error": send_result.error,
        "wa_message_id": send_result.wa_message_id,
    }
