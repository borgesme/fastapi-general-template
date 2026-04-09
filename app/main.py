from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.root import router as root_router
from app.api.v1.router import api_router
from app.db.init_db import init_db
from app.cache.redis_client import init_redis, close_redis
from app.core.exceptions import CustomHTTPException
from app.core.logger import setup_logging, get_logger
from app.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.schemas.base import ApiResponse

setup_logging()
logger = get_logger(__name__)


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

# 日志中间件（后添加的在外层，所以 RequestLogging 先添加，RequestID 后添加）
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# ---------- 全局异常处理器 ----------
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(code=exc.status_code, msg=exc.detail, data=None).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in errors)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse(code=400, msg=msg, data=None).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(code=500, msg="服务器内部错误", data=None).model_dump(),
    )


# ---------- 路由 ----------
app.include_router(root_router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health")
async def health():
    return {"status": "ok"}
