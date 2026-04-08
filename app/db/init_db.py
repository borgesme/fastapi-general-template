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
