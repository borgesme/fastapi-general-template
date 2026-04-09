import sys
from pathlib import Path
from typing import Any

import structlog
from loguru import logger as loguru_logger

from app.config import settings

# 开发模式文件句柄（延迟打开）
_dev_file_handle: Any = None


def setup_logging() -> None:
    """配置 structlog + loguru 双引擎日志系统。"""
    # 确保日志目录存在
    log_path = Path(settings.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 移除 loguru 默认 handler，避免重复日志输出
    loguru_logger.remove()

    if settings.debug:
        # 开发模式：structlog 彩色控制台输出，output_log=True 时写文件
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        ]

        # output_log=True：追加写文件（不截断 chain，返回 dict）
        if settings.output_log:
            global _dev_file_handle
            _dev_file_handle = open(log_path / f"{settings.app_name}.log", "a", encoding="utf-8")

            def _dev_file_processor(logger: Any, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
                ts = event_dict.get("timestamp", "")
                level = event_dict.get("level", "").lower()
                event = event_dict.get("event", "")
                extra = " ".join(
                    f"{k}={v}"
                    for k, v in event_dict.items()
                    if k not in ("timestamp", "level", "event", "logger")
                )
                line = f"{ts} [{level}] {name} {event}"
                if extra:
                    line += " " + extra
                _dev_file_handle.write(line + "\n")
                _dev_file_handle.flush()
                return event_dict

            processors.append(_dev_file_processor)

        processors.append(structlog.dev.ConsoleRenderer())
        structlog.configure(processors=processors)
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

        # 添加生产文件 sink：每日轮转 + gzip 压缩 + 多进程安全
        loguru_logger.add(
            f"{settings.log_dir}/{settings.app_name}.log",
            rotation="00:00",
            retention=f"{settings.log_retention_days} days",
            compression="gz",
            level=settings.log_level,
            serialize=True,
            enqueue=True,
        )
        # JSON 结构化日志同时写 stderr，供容器 stdout 采集
        loguru_logger.add(
            sys.stderr,
            level=settings.log_level,
            serialize=True,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} [{level}] {message}",
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """返回以 name 命名的 structlog logger。"""
    return structlog.get_logger(name)
