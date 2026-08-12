"""数据源站点 ORM 模型。

映射 ``cacch_ai_source_site`` 表，管理知识库下的爬取/采集站点配置。
"""

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
    """数据源站点表（``cacch_ai_source_site``）。

    记录每个知识库关联的外部站点入口、爬取策略、
    区域分类及探测状态，支持软删除。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}source_site"
    __table_args__ = (
        Index(f"ix_{AI_TABLE_PREFIX}source_site_kb_status", "kb_id", "status"),
        Index(f"ix_{AI_TABLE_PREFIX}source_site_kb_region", "kb_id", "region"),
    )

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 站点 UUID
    kb_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{AI_TABLE_PREFIX}knowledge_base.id"),
        nullable=False,
        index=True,
    )  # 所属知识库
    name: Mapped[str] = mapped_column(String(256), nullable=False)  # 站点名称
    region: Mapped[str] = mapped_column(
        String(8), nullable=False
    )  # 区域代码，如 CN / US
    category: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 站点类别，如 news / gov
    entry_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )  # 入口 URL
    crawl_mode: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 爬取模式，如 sitemap / rss
    allowed_domains: Mapped[list[Any]] = mapped_column(
        JSON, nullable=False, default=list
    )  # 允许爬取的域名白名单
    rate_limit_qps: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 请求速率限制（QPS）
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending_url"
    )  # 站点状态：pending_url / active / error 等
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # 备注
    # 以下时间为 TIMESTAMP（无时区），存 Asia/Shanghai 墙钟
    last_probe_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )  # 最近一次连通性探测时间
    last_probe_status: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # 最近一次探测结果
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
