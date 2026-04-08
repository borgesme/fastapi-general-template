from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.base import ApiResponse
from app.services.auth_service import AuthService
from app.core.security import decode_token, add_token_to_blacklist
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.helpers import TokenResponse

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=201)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(data)
    return ApiResponse(code=0, msg="注册成功", data=user)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    username: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.login(username, password)
    return ApiResponse(code=0, msg="登录成功", data=tokens)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    refresh_token: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.refresh_access_token(refresh_token)
    return ApiResponse(code=0, msg="刷新成功", data=tokens)


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    token: str,
    user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone

    payload = decode_token(token)
    exp = payload.get("exp", 0)
    jti = payload.get("jti", "")
    remain = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
    await add_token_to_blacklist(jti, remain)
    return ApiResponse(code=0, msg="已成功登出", data=None)
