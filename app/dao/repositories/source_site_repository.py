"""Source site repository."""

from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.dao.models.source_site import SourceSite


class SourceSiteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, kb_id: int, site_id: str) -> SourceSite | None:
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
        stmt = self._base_list_stmt(kb_id, keyword, region, category, status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return int(self._session.scalar(count_stmt) or 0)

    def add(self, entity: SourceSite) -> SourceSite:
        self._session.add(entity)
        self._session.flush()
        return entity

    def soft_delete(self, entity: SourceSite) -> None:
        entity.deleted_at = datetime.now(UTC)
        self._session.flush()

    def _base_list_stmt(
        self,
        kb_id: int,
        keyword: str | None,
        region: str | None,
        category: str | None,
        status: str | None,
    ) -> Select[tuple[SourceSite]]:
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
