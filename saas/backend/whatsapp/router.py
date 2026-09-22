"""
WhatsApp 路由：
  GET  /webhook              Meta 验证握手
  POST /webhook              入站消息（多租户路由）
  POST /whatsapp/connect     Embedded Signup v4 code → WABA 接入
  GET  /whatsapp/accounts    当前租户的 WABA 列表
  POST /whatsapp/send        发送审批通过的 AI 草稿
  GET  /conversations        对话列表
  GET  /conversations/{id}   对话详情 + 消息 + 待审批草稿
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.deps import get_current_user
from ..config import get_settings
from ..database import get_db
from ..models import AIDraft, Conversation, Message, User, WABAAccount
from .service import connect_waba, route_webhook, send_approved_reply

router = APIRouter(tags=["whatsapp"])


# ── Webhook verification (GET) ────────────────────────────────────────────────

@router.get("/webhook")
async def webhook_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    s = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == s.meta_webhook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Webhook inbound (POST) ────────────────────────────────────────────────────

@router.post("/webhook", status_code=200)
async def webhook_inbound(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Meta 要求 200 响应时间 < 20s。重型工作在后台线程处理。
    phone_number_id → waba_accounts → tenant 的多租户路由在 service.py 里。
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}
    result = await route_webhook(db, payload)
    return {"status": "ok", **result}


# ── Embedded Signup: connect WABA ─────────────────────────────────────────────

class ConnectIn(BaseModel):
    code: str                  # Embedded Signup v4 返回的一次性 code


class WABAOut(BaseModel):
    id: str
    waba_id: str
    phone_number_id: str
    display_phone: str
    provider: str
    status: str
    webhook_subscribed: bool


@router.post("/whatsapp/connect", response_model=WABAOut)
async def connect_whatsapp(
    body: ConnectIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Embedded Signup v4 完成后前端 POST code 到这里。
    返回已连接的 WABA 信息。
    """
    try:
        waba = await connect_waba(db, user.tenant_id, body.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return WABAOut(
        id=waba.id, waba_id=waba.waba_id,
        phone_number_id=waba.phone_number_id,
        display_phone=waba.display_phone,
        provider=waba.provider,
        status=waba.status,
        webhook_subscribed=waba.webhook_subscribed,
    )


@router.get("/whatsapp/accounts", response_model=list[WABAOut])
async def list_waba_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wabas = await db.scalars(
        select(WABAAccount).where(WABAAccount.tenant_id == user.tenant_id)
    )
    return [
        WABAOut(
            id=w.id, waba_id=w.waba_id,
            phone_number_id=w.phone_number_id,
            display_phone=w.display_phone,
            provider=w.provider,
            status=w.status,
            webhook_subscribed=w.webhook_subscribed,
        )
        for w in wabas
    ]


# ── Conversations ─────────────────────────────────────────────────────────────

class ConvSummary(BaseModel):
    id: str
    customer_name: str
    customer_phone: str | None
    country: str
    bucket: str
    status: str
    has_pending_draft: bool
    updated_at: str


class MsgOut(BaseModel):
    id: str
    role: str
    text: str
    created_at: str


class DraftOut(BaseModel):
    id: str
    text: str
    source: str
    language_code: str
    status: str


class ConvDetail(BaseModel):
    id: str
    customer_name: str
    customer_bsuid: str
    customer_phone: str | None
    country: str
    bucket: str
    messages: list[MsgOut]
    pending_draft: DraftOut | None


@router.get("/conversations", response_model=list[ConvSummary])
async def list_conversations(
    status_filter: str = Query(default="open", alias="status"),
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Conversation)
        .where(Conversation.tenant_id == user.tenant_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    if status_filter != "all":
        q = q.where(Conversation.status == status_filter)
    convs = await db.scalars(q)
    return [
        ConvSummary(
            id=c.id, customer_name=c.customer_name,
            customer_phone=c.customer_phone,
            country=c.country, bucket=c.bucket,
            status=c.status, has_pending_draft=c.has_pending_draft,
            updated_at=c.updated_at.isoformat(),
        )
        for c in convs
    ]


@router.get("/conversations/{conv_id}", response_model=ConvDetail)
async def get_conversation(
    conv_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.scalar(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.tenant_id == user.tenant_id,
        )
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs = await db.scalars(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )

    draft_row = await db.scalar(
        select(AIDraft)
        .where(AIDraft.conversation_id == conv_id, AIDraft.status == "pending")
        .order_by(AIDraft.created_at.desc())
    )

    return ConvDetail(
        id=conv.id, customer_name=conv.customer_name,
        customer_bsuid=conv.customer_bsuid,
        customer_phone=conv.customer_phone,
        country=conv.country, bucket=conv.bucket,
        messages=[
            MsgOut(id=m.id, role=m.role, text=m.text, created_at=m.created_at.isoformat())
            for m in msgs
        ],
        pending_draft=DraftOut(
            id=draft_row.id, text=draft_row.text,
            source=draft_row.source, language_code=draft_row.language_code,
            status=draft_row.status,
        ) if draft_row else None,
    )


# ── Send approved reply ───────────────────────────────────────────────────────

class SendDraftIn(BaseModel):
    draft_id: str
    final_text: str | None = None  # 销售可以修改后再发


@router.post("/whatsapp/send")
async def send_draft(
    body: SendDraftIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await send_approved_reply(db, body.draft_id, user.tenant_id, body.final_text)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Send failed"))
    return result
