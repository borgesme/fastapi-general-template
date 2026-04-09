import sys
from pathlib import Path

import structlog
from loguru import logger as loguru_logger

from app.config import settings


def setup_logging() -> None:
    """配置 structlog + loguru 双引擎日志系统。"""
    # 确保日志目录存在
    log_path = Path(settings.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 移除 loguru 默认 handler，避免重复日志输出
    loguru_logger.remove()

    if settings.debug:
        # 开发模式：structlog 彩色控制台输出
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.dev.ConsoleRenderer(),
            ],
        )
    else:
        # 生产模式：structlog JSON 输出 + loguru 文件 sink
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
        )

        # 添加文件 sink
        loguru_logger.add(
            f"{settings.log_dir}/{settings.app_name}.log",
            rotation="00:00",
            retention=f"{settings.log_retention_days} days",
            compression="gz",
            level=settings.log_level,
            serialize=True,
            enqueue=True,
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """返回以 name 命名的 structlog logger。"""
    return structlog.get_logger(name)
