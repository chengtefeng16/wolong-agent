"""
ORM 模型 — 多租户 SaaS 数据库结构
所有业务表均携带 tenant_id，查询层强制过滤。
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# Tenants
# ─────────────────────────────────────────────
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free | starter | pro
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    waba_accounts: Mapped[list["WABAAccount"]] = relationship(back_populates="tenant")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="tenant")


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(200), default="")
    password_hash: Mapped[str | None] = mapped_column(String(255))  # null if Google OAuth
    google_sub: Mapped[str | None] = mapped_column(String(255))     # Google subject id
    role: Mapped[str] = mapped_column(String(50), default="owner")  # owner | agent
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_google_sub", "google_sub"),
    )


# ─────────────────────────────────────────────
# WhatsApp Business Accounts (WABA)
# ─────────────────────────────────────────────
class WABAAccount(Base):
    """
    每个租户可拥有多个 WABA（多号码）。
    access_token_enc: 加密存储（Fernet），解密后才可用于 API 调用。
    """
    __tablename__ = "waba_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)

    # Meta identifiers
    waba_id: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(100), nullable=False)
    display_phone: Mapped[str] = mapped_column(String(50), default="")

    # Encrypted token (Fernet)
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)

    # BSP provider tag (meta_direct | twilio | dialog360)
    provider: Mapped[str] = mapped_column(String(50), default="meta_direct")

    # BSUID: Meta 2026+ 客户唯一标识（可能替代手机号）
    # 存 webhook 里的 contacts[].wa_id（系统用户 ID）
    status: Mapped[str] = mapped_column(String(50), default="active")  # active | paused | error
    webhook_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="waba_accounts")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="waba_account")

    __table_args__ = (
        UniqueConstraint("phone_number_id", name="uq_waba_phone_number_id"),
        Index("ix_waba_tenant", "tenant_id"),
    )


# ─────────────────────────────────────────────
# Conversations
# ─────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    waba_id: Mapped[str] = mapped_column(String(36), ForeignKey("waba_accounts.id"), nullable=False)

    # Customer identity — BSUID is authoritative (Meta 2026+)
    customer_bsuid: Mapped[str] = mapped_column(String(100), nullable=False)  # wa_id from webhook
    customer_phone: Mapped[str | None] = mapped_column(String(50))            # may be absent
    customer_name: Mapped[str] = mapped_column(String(200), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    language_code: Mapped[str] = mapped_column(String(10), default="en")

    # Classification
    bucket: Mapped[str] = mapped_column(String(100), default="未分类")  # 准车商|疑似车商|个人|待判断

    # State
    status: Mapped[str] = mapped_column(String(50), default="open")  # open | replied | closed
    has_pending_draft: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="conversations")
    waba_account: Mapped["WABAAccount"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.created_at"
    )
    drafts: Mapped[list["AIDraft"]] = relationship(back_populates="conversation")

    __table_args__ = (
        # One conversation per customer per WABA
        UniqueConstraint("waba_id", "customer_bsuid", name="uq_conv_waba_customer"),
        Index("ix_conv_tenant_status", "tenant_id", "status"),
        Index("ix_conv_tenant_updated", "tenant_id", "updated_at"),
    )


# ─────────────────────────────────────────────
# Messages
# ─────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)  # denormalized for fast queries

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # customer | agent
    text: Mapped[str] = mapped_column(Text, nullable=False)
    wa_message_id: Mapped[str | None] = mapped_column(String(100))  # Meta's wamid
    status: Mapped[str] = mapped_column(String(20), default="delivered")  # sent|delivered|read|failed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_msg_conversation", "conversation_id"),
        Index("ix_msg_tenant_created", "tenant_id", "created_at"),
    )


# ─────────────────────────────────────────────
# AI Drafts (pending human approval)
# ─────────────────────────────────────────────
class AIDraft(Base):
    __tablename__ = "ai_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="gemini")  # gemini|claude|rule_fallback
    language_code: Mapped[str] = mapped_column(String(10), default="en")

    # Lifecycle: pending → sent | discarded | stale
    status: Mapped[str] = mapped_column(String(20), default="pending")
    based_on_message_id: Mapped[str | None] = mapped_column(String(36))  # which customer msg triggered this
    stale: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation: Mapped["Conversation"] = relationship(back_populates="drafts")

    __table_args__ = (
        Index("ix_draft_tenant_status", "tenant_id", "status"),
    )


# ─────────────────────────────────────────────
# Usage Events (for billing metering)
# ─────────────────────────────────────────────
class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # ai_reply | cncar_lookup | wa_message_sent | waba_connected
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_usage_tenant_type", "tenant_id", "event_type"),
        Index("ix_usage_tenant_created", "tenant_id", "created_at"),
    )
