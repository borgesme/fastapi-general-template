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
