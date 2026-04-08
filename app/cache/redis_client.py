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
