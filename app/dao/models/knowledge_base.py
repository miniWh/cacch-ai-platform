"""知识库 ORM 模型。

映射 ``cacch_ai_knowledge_base`` 表，定义向量知识库的基本配置。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db_naming import AI_TABLE_PREFIX
from app.common.timeutil import now_app
from app.dao.models.base import Base


class KnowledgeBase(Base):
    """知识库表（``cacch_ai_knowledge_base``）。

    存储知识库名称、嵌入模型配置及启用状态，
    作为数据源站点与聊天会话的外键父表。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}knowledge_base"

    # Integer + autoincrement：SQLite/PostgreSQL 均可自增；PG 库脚本仍可用 BIGSERIAL
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # 知识库名称
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    embedding_model: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # 向量嵌入模型标识
    embedding_dim: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2048
    )  # 嵌入向量维度
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # 1=启用，0=停用
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
