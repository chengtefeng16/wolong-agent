"""
Auth service: JWT 签发/验证 + bcrypt 密码哈希 + Google OAuth token 验证
"""
from __future__ import annotations

import httpx
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Tenant, User

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    return jwt.encode(
        {**payload, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ── Registration / Login ──────────────────────────────────────────────────────

async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str,
    tenant_name: str,
) -> tuple[Tenant, User]:
    """Create a new tenant + owner user. Raises ValueError on duplicate email."""
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise ValueError("Email already registered")

    tenant = Tenant(name=tenant_name)
    db.add(tenant)
    await db.flush()  # get tenant.id

    user = User(
        tenant_id=tenant.id,
        email=email,
        name=name,
        password_hash=hash_password(password),
        role="owner",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return tenant, user


async def login_user(db: AsyncSession, email: str, password: str) -> User:
    """Returns User if credentials valid. Raises ValueError otherwise."""
    user = await db.scalar(select(User).where(User.email == email, User.is_active == True))
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return user


# ── Google OAuth ──────────────────────────────────────────────────────────────

async def google_login(db: AsyncSession, id_token: str) -> tuple[User, bool]:
    """
    Verify Google id_token, upsert user. Returns (user, is_new).
    Frontend sends the id_token from Google Sign-In.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
        r.raise_for_status()
        info = r.json()

    google_sub = info["sub"]
    email = info.get("email", "")
    name = info.get("name", email.split("@")[0])

    user = await db.scalar(select(User).where(User.google_sub == google_sub))
    if user:
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user, False

    # Check if user exists by email (link accounts)
    user = await db.scalar(select(User).where(User.email == email))
    if user:
        user.google_sub = google_sub
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user, False

    # New user → create tenant + user
    tenant = Tenant(name=f"{name}'s workspace")
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        name=name,
        google_sub=google_sub,
        role="owner",
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True
