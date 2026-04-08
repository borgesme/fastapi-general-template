import uuid
from datetime import datetime
from pydantic import EmailStr, field_validator

from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError("用户名长度为 3-50 个字符")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少 8 个字符")
        return v


class UserUpdate(BaseSchema):
    username: str | None = None
    email: EmailStr | None = None


class UserPasswordUpdate(BaseSchema):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("新密码长度至少 8 个字符")
        return v


class UserResponse(BaseSchema):
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
