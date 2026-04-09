import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog.contextvars

from app.core.logger import get_logger

log = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """生成 request_id 并绑定到结构化日志上下文。"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
