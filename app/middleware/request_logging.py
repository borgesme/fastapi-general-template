import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logger import get_logger

log = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """优先从 X-Forwarded-For 获取真实 IP。"""
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录请求方法、路径、状态码、响应耗时。"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        log.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client_ip=get_client_ip(request),
        )
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
