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
