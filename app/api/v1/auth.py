from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.core.security import decode_token, add_token_to_blacklist
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.helpers import TokenResponse, MsgResponse

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    username: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.login(username, password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.refresh_access_token(refresh_token)
    return tokens


@router.post("/logout", response_model=MsgResponse)
async def logout(
    token: str,
    user: User = Depends(get_current_user),
):
    """登出：将 access_token jti 加入黑名单"""
    from datetime import datetime, timezone

    payload = decode_token(token)
    exp = payload.get("exp", 0)
    jti = payload.get("jti", "")
    remain = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
    await add_token_to_blacklist(jti, remain)
    return MsgResponse(msg="已成功登出")
