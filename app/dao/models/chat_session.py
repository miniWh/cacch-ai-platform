"""聊天会话与消息 ORM 模型。

映射 ``cacch_ai_chat_session`` 与 ``cacch_ai_chat_message`` 表，
用于 RAG 对话的历史记录存储。
"""

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
    """聊天会话表（``cacch_ai_chat_session``）。

    按知识库维度管理对话线程，支持置顶、标题锁定与软删除。
    """

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

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 会话 UUID
    kb_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{AI_TABLE_PREFIX}knowledge_base.id"),
        nullable=False,
        index=True,
    )  # 所属知识库
    app_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 预留应用 ID
    user_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # 发起用户标识
    title: Mapped[str] = mapped_column(String(128), nullable=False, default="新对话")
    title_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # 锁定后不再自动更新标题
    pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # 是否置顶
    pinned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )  # 置顶时间，用于排序
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
    )  # 软删除时间戳


class ChatMessage(Base):
    """聊天消息表（``cacch_ai_chat_message``）。

    存储单条对话消息及其 RAG 引用（citations）元数据。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}chat_message"
    __table_args__ = (
        Index(
            f"ix_{AI_TABLE_PREFIX}chat_message_session_created",
            "session_id",
            "created_at",
        ),
    )

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 消息 UUID
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(f"{AI_TABLE_PREFIX}chat_session.session_id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # 消息角色：user / assistant / system
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 消息正文
    citations_json: Mapped[list[Any] | None] = mapped_column(
        JSON, nullable=True
    )  # RAG 引用片段列表
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
