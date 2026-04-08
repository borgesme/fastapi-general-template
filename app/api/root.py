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
