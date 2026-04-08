import uuid
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedError, ConflictError
from app.utils.helpers import TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_register(self, data: UserCreate) -> User:
        stmt = select(User).where(User.username == data.username)
        result = self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("用户名已存在")

        stmt = select(User).where(User.email == data.email)
        result = self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("邮箱已被注册")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    async def register(self, data: UserCreate) -> User:
        return await asyncio.to_thread(self._sync_register, data)

    def _sync_login(self, username: str, password: str) -> TokenResponse:
        stmt = select(User).where(User.username == username)
        result = self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("用户名或密码错误")

        if not user.is_active:
            raise UnauthorizedError("用户已被禁用")

        access_token, _ = create_access_token(user.id, {"username": user.username})
        refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, username: str, password: str) -> TokenResponse:
        return await asyncio.to_thread(self._sync_login, username, password)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        from app.core.security import decode_token, is_token_blacklisted

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("无效的 refresh token")

        jti = payload.get("jti")
        if jti and await is_token_blacklisted(jti):
            raise UnauthorizedError("Token 已失效")

        user_id = uuid.UUID(payload["sub"])
        stmt = select(User).where(User.id == user_id)
        result = self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("用户无效或已禁用")

        access_token, _ = create_access_token(user.id, {"username": user.username})

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
