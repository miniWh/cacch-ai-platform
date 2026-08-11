"""knowledge_base table (physical: cacch_ai_knowledge_base)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db_naming import AI_TABLE_PREFIX
from app.common.timeutil import now_app
from app.dao.models.base import Base


class KnowledgeBase(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}knowledge_base"

    # Integer + autoincrement：SQLite/PostgreSQL 均可自增；PG 库脚本仍可用 BIGSERIAL
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=2048)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # TIMESTAMP WITHOUT TIME ZONE：存 Asia/Shanghai 墙钟，避免 IDE 按库默认 -04 展示
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        onupdate=now_app,
        server_default=func.now(),
    )
