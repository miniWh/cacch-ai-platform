"""chat_session / chat_message tables."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
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


class ChatSession(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}chat_session"
    __table_args__ = (
        Index(
            f"ix_{AI_TABLE_PREFIX}chat_session_kb_alive",
            "kb_id",
            "pinned",
            "pinned_at",
            "updated_at",
        ),
    )

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kb_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{AI_TABLE_PREFIX}knowledge_base.id"),
        nullable=False,
        index=True,
    )
    app_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False, default="新对话")
    title_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pinned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
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


class ChatMessage(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}chat_message"
    __table_args__ = (
        Index(
            f"ix_{AI_TABLE_PREFIX}chat_message_session_created",
            "session_id",
            "created_at",
        ),
    )

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(f"{AI_TABLE_PREFIX}chat_session.session_id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
