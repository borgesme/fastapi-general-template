# FastAPI 微服务模板 — 实施计划

> **For agentic workers:** 使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 执行本计划。步骤使用 `- [ ]` 复选框语法追踪进度。

**目标：** 搭建 FastAPI 微服务模板骨架，完成基础认证（JWT）和用户管理模块。

**架构概述：** 单体应用，三层架构（API → Service → DB）。使用 SQLAlchemy Core 2.x + Alembic 管理数据库，Pydantic Settings 管理配置，Redis 存储 JWT 黑名单。

**技术栈：** FastAPI 0.110+ / SQLAlchemy 2.0+ / Alembic 1.13+ / PostgreSQL / Redis / PyJWT / python-jose / bcrypt / Pydantic v2 / structlog / SQLAlchemy-Utils

---

## 文件结构总览

```
app/
├── __init__.py
├── main.py
├── config.py
├── dependencies.py
├── api/
│   ├── __init__.py
│   ├── root.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py
│       ├── auth.py
│       └── users.py
├── core/
│   ├── __init__.py
│   ├── security.py
│   └── exceptions.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   └── order.py
├── schemas/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   └── order.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   └── order_service.py
├── db/
│   ├── __init__.py
│   ├── session.py
│   └── init_db.py
├── cache/
│   ├── __init__.py
│   └── redis_client.py
└── utils/
    ├── __init__.py
    └── helpers.py

alembic/
├── alembic.ini
├── env.py
└── versions/

tests/
├── __init__.py
├── conftest.py
├── test_auth.py
└── test_users.py

.env.example
requirements.txt
```

---

## Task 1: 项目初始化 — 依赖文件和环境变量模板

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`（空文件，仅标记为 Python 包）

- [ ] **Step 1: 创建 `requirements.txt`**

```txt
# Web Framework
fastapi>=0.110.0
uvicorn[standard]>=0.27.0

# Database
sqlalchemy>=2.0.25
alembic>=1.13.1
psycopg2-binary>=2.9.9
sqlalchemy-utils>=0.41.2

# Redis
redis>=5.0.1

# Auth
PyJWT>=2.8.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.1.2

# Validation & Config
pydantic>=2.6.0
pydantic-settings>=2.1.0
email-validator>=2.1.0

# Logging
structlog>=24.1.0
loguru>=0.7.2

# Utils
python-multipart>=0.0.9

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.4
httpx>=0.27.0
```

- [ ] **Step 2: 创建 `.env.example`**

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_project

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (生成方式: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
APP_NAME=FastAPI Project
DEBUG=true
```

- [ ] **Step 3: 提交**

```bash
git add requirements.txt .env.example app/__init__.py
git commit -m "chore: add requirements.txt and .env.example"
```

---

## Task 2: 配置模块 — `app/config.py`

**Files:**
- Create: `app/config.py`

- [ ] **Step 1: 创建 `app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "FastAPI Project"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fastapi_project"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()
```

- [ ] **Step 2: 提交**

```bash
git add app/config.py
git commit -m "feat: add pydantic settings configuration module"
```

---

## Task 3: 数据库层 — `app/db/session.py` + `app/db/init_db.py`

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/session.py`
- Create: `app/db/init_db.py`

- [ ] **Step 1: 创建 `app/db/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `app/db/session.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """数据库 Session 依赖注入，供 FastAPI Depends() 使用。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 创建 `app/db/init_db.py`**

```python
import structlog

from app.db.session import engine

logger = structlog.get_logger()


def init_db():
    """测试数据库连接是否正常。"""
    try:
        with engine.connect() as conn:
            logger.info("database_connection_ok")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise
```

- [ ] **Step 4: 提交**

```bash
git add app/db/
git commit -m "feat: add database session management and connection test"
```

---

## Task 4: Redis 缓存层 — `app/cache/redis_client.py`

**Files:**
- Create: `app/cache/__init__.py`
- Create: `app/cache/redis_client.py`

- [ ] **Step 1: 创建 `app/cache/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `app/cache/redis_client.py`**

```python
import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger()

redis_async: redis.Redis | None = None


async def init_redis() -> None:
    global redis_async
    redis_async = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        await redis_async.ping()
        logger.info("redis_connection_ok")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        raise


async def close_redis() -> None:
    global redis_async
    if redis_async:
        await redis_async.aclose()
        logger.info("redis_connection_closed")


def get_redis() -> redis.Redis:
    if redis_async is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_async
```

- [ ] **Step 3: 提交**

```bash
git add app/cache/
git commit -m "feat: add async redis client with connection management"
```

---

## Task 5: 数据库模型基类 — `app/models/base.py`

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/base.py`
- Modify: `app/db/session.py`（导入 Base）

- [ ] **Step 1: 创建 `app/models/__init__.py`**

```python
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.order import Order  # noqa: F401

__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin", "User", "Order"]
```

- [ ] **Step 2: 创建 `app/models/base.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Boolean, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """所有模型的基类。"""
    pass


class TimestampMixin:
    """自动填充 created_at 和 updated_at。"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """软删除标记。"""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 3: 修改 `app/db/session.py`，在文件末尾添加一行**

```python
# 文件底部添加：
from app.models.base import Base  # noqa: F401
```

- [ ] **Step 4: 提交**

```bash
git add app/models/
git commit -m "feat: add base models with TimestampMixin and SoftDeleteMixin"
```

---

## Task 6: User 模型 — `app/models/user.py`

**Files:**
- Create: `app/models/user.py`

- [ ] **Step 1: 创建 `app/models/user.py`**

```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    orders = relationship("Order", back_populates="user")
```

- [ ] **Step 2: 提交**

```bash
git add app/models/user.py
git commit -m "feat: add User ORM model"
```

---

## Task 7: Order 模型（占位）— `app/models/order.py`

**Files:**
- Create: `app/models/order.py`

- [ ] **Step 1: 创建 `app/models/order.py`**

```python
import uuid
import enum
from decimal import Decimal

from sqlalchemy import String, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Order(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    user = relationship("User", back_populates="orders")
```

- [ ] **Step 2: 提交**

```bash
git add app/models/order.py
git commit -m "feat(order): add Order model placeholder for future implementation"
```

---

## Task 8: Pydantic Schema — `app/schemas/base.py` + `app/schemas/user.py` + `app/schemas/order.py`

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/base.py`
- Create: `app/schemas/user.py`
- Create: `app/schemas/order.py`

- [ ] **Step 1: 创建 `app/schemas/__init__.py`**

```python
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPasswordUpdate,
)
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)
from app.schemas.base import PageResponse, PageParams

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserPasswordUpdate",
    "OrderCreate", "OrderUpdate", "OrderResponse",
    "PageResponse", "PageParams",
]
```

- [ ] **Step 2: 创建 `app/schemas/base.py`**

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 3: 创建 `app/schemas/user.py`**

```python
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
```

- [ ] **Step 4: 创建 `app/schemas/order.py`**

```python
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import field_validator

from app.models.order import OrderStatus
from app.schemas.base import BaseSchema


class OrderBase(BaseSchema):
    title: str
    amount: Decimal


class OrderCreate(OrderBase):
    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("订单金额必须大于 0")
        return v


class OrderUpdate(BaseSchema):
    title: str | None = None
    amount: Decimal | None = None
    status: OrderStatus | None = None


class OrderResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    amount: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 5: 提交**

```bash
git add app/schemas/
git commit -m "feat: add pydantic schemas for users and orders"
```

---

## Task 9: 核心安全模块 — `app/core/security.py`

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/security.py`

- [ ] **Step 1: 创建 `app/core/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `app/core/security.py`**

```python
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import structlog
from passlib.context import CryptContext

from app.config import settings
from app.cache.redis_client import get_redis

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID, extra_claims: dict | None = None) -> tuple[str, str]:
    """创建 access_token，返回 (token, jti)"""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "access",
        "exp": expire,
        **(extra_claims or {}),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    """创建 refresh_token，返回 (token, jti)"""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "exp": expire,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


async def add_token_to_blacklist(jti: str, expire_seconds: int) -> None:
    """将 JWT jti 加入 Redis 黑名单"""
    redis = get_redis()
    await redis.setex(f"blacklist:{jti}", expire_seconds, "1")
    logger.info("token_blacklisted", jti=jti, ttl_seconds=expire_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """检查 JWT jti 是否在黑名单中"""
    redis = get_redis()
    result = await redis.exists(f"blacklist:{jti}")
    return result > 0
```

- [ ] **Step 3: 提交**

```bash
git add app/core/
git commit -m "feat: add JWT security module with password hashing and Redis blacklist"
```

---

## Task 10: 全局异常处理 — `app/core/exceptions.py`

**Files:**
- Create: `app/core/exceptions.py`

- [ ] **Step 1: 创建 `app/core/exceptions.py`**

```python
from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(CustomHTTPException):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(CustomHTTPException):
    def __init__(self, detail: str = "未授权"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(CustomHTTPException):
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestError(CustomHTTPException):
    def __init__(self, detail: str = "请求参数错误"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictError(CustomHTTPException):
    def __init__(self, detail: str = "资源冲突"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
```

- [ ] **Step 2: 提交**

```bash
git add app/core/exceptions.py
git commit -m "feat: add custom exception classes for unified error handling"
```

---

## Task 11: 工具函数 — `app/utils/helpers.py`

**Files:**
- Create: `app/utils/__init__.py`
- Create: `app/utils/helpers.py`

- [ ] **Step 1: 创建 `app/utils/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `app/utils/helpers.py`**

```python
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MsgResponse(BaseModel):
    msg: str
```

- [ ] **Step 3: 提交**

```bash
git add app/utils/
git commit -m "feat: add utility helpers and response schemas"
```

---

## Task 12: 服务层 — `app/services/auth_service.py`

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/auth_service.py`

- [ ] **Step 1: 创建 `app/services/__init__.py`**

```python
from app.services.auth_service import AuthService
from app.services.user_service import UserService

__all__ = ["AuthService", "UserService"]
```

- [ ] **Step 2: 创建 `app/services/auth_service.py`**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedError, ConflictError
from app.utils.helpers import TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserCreate) -> User:
        # 检查用户名是否存在
        stmt = select(User).where(User.username == data.username)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("用户名已存在")

        # 检查邮箱是否存在
        stmt = select(User).where(User.email == data.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("邮箱已被注册")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("用户名或密码错误")

        if not user.is_active:
            raise UnauthorizedError("用户已被禁用")

        access_token, _ = create_access_token(user.id, {"username": user.username})
        refresh_token, _ = create_refresh_token(user.id)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

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
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("用户无效或已禁用")

        access_token, _ = create_access_token(user.id, {"username": user.username})

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
```

- [ ] **Step 3: 提交**

```bash
git add app/services/auth_service.py
git commit -m "feat: add auth service with register, login, and refresh token"
```

---

## Task 13: 用户服务 — `app/services/user_service.py`

**Files:**
- Create: `app/services/user_service.py`

- [ ] **Step 1: 创建 `app/services/user_service.py`**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import hash_password, verify_password
from app.core.exceptions import NotFoundError, BadRequestError


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("用户不存在")
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        if data.username is not None:
            stmt = select(User).where(User.username == data.username, User.id != user.id)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise BadRequestError("用户名已被使用")
            user.username = data.username

        if data.email is not None:
            stmt = select(User).where(User.email == data.email, User.id != user.id)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise BadRequestError("邮箱已被使用")
            user.email = data.email

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise BadRequestError("原密码错误")

        user.hashed_password = hash_password(new_password)
        await self.db.commit()
```

- [ ] **Step 2: 提交**

```bash
git add app/services/user_service.py
git commit -m "feat: add user service with update and password change"
```

---

## Task 14: 订单服务（占位）— `app/services/order_service.py`

**Files:**
- Create: `app/services/order_service.py`

- [ ] **Step 1: 创建 `app/services/order_service.py`**

```python
"""
订单服务（预留模块，Phase 2 实现）
"""
from app.services.user_service import UserService

__all__ = ["UserService"]
```

- [ ] **Step 2: 提交**

```bash
git add app/services/order_service.py
git commit -m "feat(order): add order service placeholder"
```

---

## Task 15: 依赖注入 — `app/dependencies.py`

**Files:**
- Create: `app/dependencies.py`

- [ ] **Step 1: 创建 `app/dependencies.py`**

```python
import uuid
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

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
    检查：签名 → 黑名单 → 用户是否存在 → 是否激活
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

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """仅允许活跃用户访问"""
    if not user.is_active:
        raise ForbiddenError("用户已被禁用")
    return user
```

- [ ] **Step 2: 提交**

```bash
git add app/dependencies.py
git commit -m "feat: add dependency injection for auth (get_current_user)"
```

---

## Task 16: API 路由 — `app/api/root.py` + `app/api/v1/auth.py`

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/root.py`
- Create: `app/api/v1/__init__.py`
- Create: `app/api/v1/router.py`
- Create: `app/api/v1/auth.py`

- [ ] **Step 1: 创建 `app/api/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `app/api/root.py`**

```python
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.cache.redis_client import get_redis

logger = structlog.get_logger()
router = APIRouter(tags=["健康检查"])


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """健康检查：DB + Redis 连通性"""
    db_status = "ok"
    redis_status = "ok"

    try:
        await db.connection()
    except Exception as e:
        db_status = f"error: {e}"
        logger.error("health_db_failed", error=str(e))

    try:
        redis = get_redis()
        await redis.ping()
    except Exception as e:
        redis_status = f"error: {e}"
        logger.error("health_redis_failed", error=str(e))

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=overall, database=db_status, redis=redis_status)
```

- [ ] **Step 3: 创建 `app/api/v1/__init__.py`**

```python
```

- [ ] **Step 4: 创建 `app/api/v1/router.py`**

```python
from fastapi import APIRouter

from app.api.v1 import auth, users, orders

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(orders.router)
```

- [ ] **Step 5: 创建 `app/api/v1/auth.py`**

```python
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
    token: str = Depends(lambda credentials: credentials.credentials),
    user: User = Depends(get_current_user),
):
    """登出：将 access_token jti 加入黑名单"""
    payload = decode_token(token)
    import time
    from datetime import datetime, timezone
    exp = payload.get("exp", 0)
    jti = payload.get("jti", "")
    remain = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
    await add_token_to_blacklist(jti, remain)
    return MsgResponse(msg="已成功登出")
```

- [ ] **Step 6: 提交**

```bash
git add app/api/
git commit -m "feat: add API routes for health check and authentication"
```

---

## Task 17: 用户 API + 订单占位路由

**Files:**
- Create: `app/api/v1/users.py`
- Create: `app/api/v1/orders.py`

- [ ] **Step 1: 创建 `app/api/v1/users.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserUpdate, UserResponse, UserPasswordUpdate
from app.services.user_service import UserService
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.helpers import MsgResponse

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    updated = await service.update(user, data)
    return updated


@router.put("/me/password", response_model=MsgResponse)
async def change_password(
    data: UserPasswordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.update_password(user, data.old_password, data.new_password)
    return MsgResponse(msg="密码修改成功")
```

- [ ] **Step 2: 创建 `app/api/v1/orders.py`（占位）**

```python
"""
订单 API（预留模块，Phase 2 实现）
"""
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/orders", tags=["订单管理"])
```

- [ ] **Step 3: 提交**

```bash
git add app/api/v1/users.py app/api/v1/orders.py
git commit -m "feat: add users API and orders placeholder route"
```

---

## Task 18: 应用入口 — `app/main.py`

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: 创建 `app/main.py`**

```python
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.root import router as root_router
from app.api.v1.router import api_router
from app.db.init_db import init_db
from app.cache.redis_client import init_redis, close_redis

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", app=settings.app_name)
    init_db()
    await init_redis()
    logger.info("app_started")
    yield
    await close_redis()
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}
```

- [ ] **Step 2: 提交**

```bash
git add app/main.py
git commit -m "feat: add FastAPI main application entry with lifespan hooks"
```

---

## Task 19: Alembic 迁移初始化

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Modify: `app/db/session.py`（添加迁移导入）

- [ ] **Step 1: 初始化 Alembic（在项目根目录运行）**

```bash
# 在项目根目录运行
alembic init alembic
```

- [ ] **Step 2: 修改 `alembic.ini`**（找到 `sqlalchemy.url` 行，设置为空，后续在 `env.py` 中读取）

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

- [ ] **Step 3: 修改 `alembic/env.py`**

```python
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

from app.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.order import Order

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

- [ ] **Step 4: 修改 `alembic/script.py.mako`**（在升级标记处添加 upgrade 和 downgrade 函数签名）

默认内容无需修改，alembic generate 会自动填充。

- [ ] **Step 5: 生成首次迁移脚本**

```bash
alembic revision --autogenerate -m "initial migration"
```

- [ ] **Step 6: 提交**

```bash
git add alembic/ alembic.ini
git add alembic/versions/  # 包含生成的迁移文件
git commit -m "chore: add alembic migration setup and initial migration"
```

---

## Task 20: 测试框架 + 认证测试

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`
- Create: `tests/test_users.py`

- [ ] **Step 1: 创建 `tests/__init__.py`**

```python
```

- [ ] **Step 2: 创建 `tests/conftest.py`**

```python
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import Base, get_db
from app.config import settings

# 使用 SQLite 测试数据库（异步）
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 3: 创建 `tests/test_auth.py`**

```python
import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "another@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
        },
    )
    # 登录
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpw",
            "email": "wrongpw@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpw", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
```

- [ ] **Step 4: 创建 `tests/test_users.py`**

```python
import pytest


async def get_access_token(client, username="meuser", email="me@example.com", password="password123"):
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_get_me(client):
    token = await get_access_token(client)
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_me(client):
    token = await get_access_token(client, username="updateme", email="update@example.com")
    resp = await client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "updatedname"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "updatedname"


@pytest.mark.asyncio
async def test_change_password(client):
    token = await get_access_token(
        client, username="chgpw", email="chgpw@example.com", password="oldpassword"
    )
    resp = await client.put(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "oldpassword", "new_password": "newpassword123"},
    )
    assert resp.status_code == 200

    # 新密码登录验证
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "chgpw", "password": "newpassword123"},
    )
    assert login_resp.status_code == 200
```

- [ ] **Step 5: 提交**

```bash
git add tests/
git commit -m "test: add pytest fixtures and tests for auth and users API"
```

---

## Task 21: 项目收尾 — README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 `README.md`**

```markdown
# FastAPI 微服务模板

基于 FastAPI + SQLAlchemy + PostgreSQL + Redis 的单体应用模板。

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写数据库和 Redis 连接信息
# 生成 SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 数据库迁移

```bash
alembic upgrade head
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问: http://localhost:8000/docs （Swagger UI）

## API 文档

| 路径 | 说明 |
|------|------|
| GET /health | 健康检查 |
| POST /api/v1/auth/register | 用户注册 |
| POST /api/v1/auth/login | 用户登录 |
| POST /api/v1/auth/refresh | 刷新 Token |
| POST /api/v1/auth/logout | 登出 |
| GET /api/v1/users/me | 获取当前用户 |
| PUT /api/v1/users/me | 更新个人资料 |
| PUT /api/v1/users/me/password | 修改密码 |

## 运行测试

```bash
pip install aiosqlite
pytest -v
```
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add README with quickstart guide"
```

---

## 实施检查清单

- [ ] Task 1: `requirements.txt` + `.env.example`
- [ ] Task 2: `app/config.py`
- [ ] Task 3: `app/db/session.py` + `app/db/init_db.py`
- [ ] Task 4: `app/cache/redis_client.py`
- [ ] Task 5: `app/models/base.py`
- [ ] Task 6: `app/models/user.py`
- [ ] Task 7: `app/models/order.py`
- [ ] Task 8: `app/schemas/`
- [ ] Task 9: `app/core/security.py`
- [ ] Task 10: `app/core/exceptions.py`
- [ ] Task 11: `app/utils/helpers.py`
- [ ] Task 12: `app/services/auth_service.py`
- [ ] Task 13: `app/services/user_service.py`
- [ ] Task 14: `app/services/order_service.py`
- [ ] Task 15: `app/dependencies.py`
- [ ] Task 16: `app/api/root.py` + `app/api/v1/auth.py`
- [ ] Task 17: `app/api/v1/users.py` + `app/api/v1/orders.py`
- [ ] Task 18: `app/main.py`
- [ ] Task 19: Alembic 初始化 + 首次迁移
- [ ] Task 20: 测试框架 + 测试用例
- [ ] Task 21: README.md

---

## 执行方式选择

计划已保存到 `docs/superpowers/plans/2026-04-08-fastapi-microservice-template-plan.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** — 我派发子代理逐任务执行，任务间做检查点确认

**2. Inline Execution（当前会话执行）** — 我在当前会话中按批次执行，批次间汇报进度

你想用哪种方式？
