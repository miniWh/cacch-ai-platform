"""数据源站点仓储。

封装知识库下采集站点的查询、创建与软删除操作。
"""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.common.timeutil import now_app
from app.dao.models.source_site import SourceSite


class SourceSiteRepository:
    """数据源站点仓储。

    管理 ``SourceSite`` 实体的 CRUD 及条件筛选。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, kb_id: int, site_id: str) -> SourceSite | None:
        """按知识库 ID 与站点 ID 查询未删除的站点。"""
        stmt = select(SourceSite).where(
            SourceSite.kb_id == kb_id,
            SourceSite.site_id == site_id,
            SourceSite.deleted_at.is_(None),
        )
        return self._session.scalar(stmt)

    def list(
        self,
        kb_id: int,
        *,
        keyword: str | None = None,
        region: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[SourceSite]:
        """按条件列出站点（名称升序）。"""
        stmt = self._base_list_stmt(kb_id, keyword, region, category, status)
        stmt = stmt.order_by(SourceSite.name.asc())
        return list(self._session.scalars(stmt))

    def count(
        self,
        kb_id: int,
        *,
        keyword: str | None = None,
        region: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> int:
        """按相同筛选条件统计站点数量。"""
        stmt = self._base_list_stmt(kb_id, keyword, region, category, status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return int(self._session.scalar(count_stmt) or 0)

    def add(self, entity: SourceSite) -> SourceSite:
        """新增站点并 flush。"""
        self._session.add(entity)
        self._session.flush()
        return entity

    def soft_delete(self, entity: SourceSite) -> None:
        """软删除站点（设置 ``deleted_at``）。"""
        entity.deleted_at = now_app()
        self._session.flush()

    def _base_list_stmt(
        self,
        kb_id: int,
        keyword: str | None,
        region: str | None,
        category: str | None,
        status: str | None,
    ) -> Select[tuple[SourceSite]]:
        """构建站点列表/计数的公共筛选语句（排除已软删除）。"""
        stmt = select(SourceSite).where(
            SourceSite.kb_id == kb_id,
            SourceSite.deleted_at.is_(None),
        )
        if keyword:
            like = f"%{keyword.strip()}%"
            stmt = stmt.where(
                (SourceSite.name.ilike(like)) | (SourceSite.entry_url.ilike(like))
            )
        if region:
            stmt = stmt.where(SourceSite.region == region)
        if category:
            stmt = stmt.where(SourceSite.category == category)
        if status:
            stmt = stmt.where(SourceSite.status == status)
        return stmt
