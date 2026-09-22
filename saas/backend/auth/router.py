from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .service import create_access_token, google_login, login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleIn(BaseModel):
    id_token: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    name: str
    is_new: bool = False


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    try:
        tenant, user = await register_user(db, body.email, body.password, body.name, body.company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_access_token({"sub": user.id, "tenant_id": tenant.id})
    return TokenOut(access_token=token, user_id=user.id, tenant_id=tenant.id, name=user.name, is_new=True)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    try:
        user = await login_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id})
    return TokenOut(access_token=token, user_id=user.id, tenant_id=user.tenant_id, name=user.name)


@router.post("/google", response_model=TokenOut)
async def google_auth(body: GoogleIn, db: AsyncSession = Depends(get_db)):
    try:
        user, is_new = await google_login(db, body.id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google auth failed: {e}")
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id})
    return TokenOut(
        access_token=token, user_id=user.id, tenant_id=user.tenant_id,
        name=user.name, is_new=is_new,
    )
