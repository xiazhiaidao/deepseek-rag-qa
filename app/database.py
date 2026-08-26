"""SQLAlchemy 数据库引擎与会话管理。"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

DB_URL = settings.chat_db_url

if DB_URL.startswith("sqlite"):
    # 确保 SQLite 文件所在目录存在
    raw_path = DB_URL.replace("sqlite:///", "", 1)
    if raw_path and not raw_path.startswith("/") and ":" not in raw_path.split("/")[0]:
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # MySQL / PostgreSQL 等
    engine = create_engine(DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def init_db() -> None:
    """建表（幂等）。"""
    from . import models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖：请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()