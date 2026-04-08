import uuid
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import hash_password, verify_password
from app.core.exceptions import NotFoundError, BadRequestError


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_get_by_id(self, user_id: uuid.UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        result = self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("用户不存在")
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        return await asyncio.to_thread(self._sync_get_by_id, user_id)

    def _sync_update(self, user: User, data: UserUpdate) -> User:
        if data.username is not None:
            stmt = select(User).where(User.username == data.username, User.id != user.id)
            result = self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise BadRequestError("用户名已被使用")
            user.username = data.username

        if data.email is not None:
            stmt = select(User).where(User.email == data.email, User.id != user.id)
            result = self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise BadRequestError("邮箱已被使用")
            user.email = data.email

        self.db.commit()
        self.db.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        return await asyncio.to_thread(self._sync_update, user, data)

    def _sync_update_password(self, user: User, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise BadRequestError("原密码错误")
        user.hashed_password = hash_password(new_password)
        self.db.commit()

    async def update_password(self, user: User, old_password: str, new_password: str) -> None:
        await asyncio.to_thread(self._sync_update_password, user, old_password, new_password)
