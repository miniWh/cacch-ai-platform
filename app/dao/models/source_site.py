"""source_site table (physical: cacch_ai_source_site)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db_naming import AI_TABLE_PREFIX
from app.common.timeutil import now_app
from app.dao.models.base import Base


class SourceSite(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}source_site"
    __table_args__ = (
        Index(f"ix_{AI_TABLE_PREFIX}source_site_kb_status", "kb_id", "status"),
        Index(f"ix_{AI_TABLE_PREFIX}source_site_kb_region", "kb_id", "region"),
    )

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kb_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{AI_TABLE_PREFIX}knowledge_base.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    crawl_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    allowed_domains: Mapped[list[Any]] = mapped_column(
        JSON, nullable=False, default=list
    )
    rate_limit_qps: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending_url"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 以下时间为 TIMESTAMP（无时区），存 Asia/Shanghai 墙钟
    last_probe_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    last_probe_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
