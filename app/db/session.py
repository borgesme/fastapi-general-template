from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """数据库 Session 依赖注入，供 FastAPI Depends() 使用。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.models.base import Base  # noqa: F401
