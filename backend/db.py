"""数据库层：本地 SQLite，生产环境可用 Neon PostgreSQL（通过 DATABASE_URL 切换）。"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# 本地默认使用 SQLite（路径固定在后端目录，避免受启动目录影响）；部署时设置 DATABASE_URL 切换 PostgreSQL
_DEFAULT_SQLITE = "sqlite:///" + os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "calculator.db"
).replace("\\", "/")
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    """返回当前 UTC 时间（去掉 tzinfo，避免 SQLite 存储时丢失时区导致不一致）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def serialize_dt(dt: datetime) -> str:
    """把数据库时间序列化为带时区的 ISO-8601 字符串（UTC），前端负责转本地时间。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expression: Mapped[str] = mapped_column(String(200), nullable=False)
    result: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # 联合索引保证稳定的倒序排序
    __table_args__ = (Index("ix_created_at_id", "created_at", "id"),)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
