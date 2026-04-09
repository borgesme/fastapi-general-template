import uuid

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import structlog.contextvars

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token, is_token_blacklisted
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.services.user_service import UserService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 JWT Token 中解析用户信息并注入。
    检查：签名 -> 黑名单 -> 用户是否存在 -> 是否激活
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise UnauthorizedError("无效的 access token")

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise UnauthorizedError("Token 已失效")

    user_id = uuid.UUID(payload["sub"])
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user.is_active:
        raise ForbiddenError("用户已被禁用")

    structlog.contextvars.bind_contextvars(user_id=str(user.id))
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """仅允许活跃用户访问"""
    if not user.is_active:
        raise ForbiddenError("用户已被禁用")
    return user
