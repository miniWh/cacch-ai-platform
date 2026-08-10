"""Source site business service."""

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationAppError
from app.dao.models.source_site import SourceSite
from app.dao.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.dao.repositories.source_site_repository import SourceSiteRepository
from app.rag.loader.probe import apply_probe_result, probe_site
from app.service.schemas.source import (
    ProbeRequest,
    ProbeResponse,
    ProbeResultItem,
    SourceListOut,
    SourceSiteCreate,
    SourceSiteOut,
    SourceSiteUpdate,
)
from app.web.config import Settings, get_settings


class SourceService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._sources = SourceSiteRepository(session)
        self._kbs = KnowledgeBaseRepository(session)

    def list_sources(
        self,
        kb_id: int,
        *,
        keyword: str | None = None,
        region: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> SourceListOut:
        self._require_kb(kb_id)
        items = self._sources.list(
            kb_id,
            keyword=keyword,
            region=region,
            category=category,
            status=status,
        )
        return SourceListOut(
            items=[SourceSiteOut.model_validate(i) for i in items],
            total=len(items),
        )

    def get_source(self, kb_id: int, site_id: str) -> SourceSiteOut:
        self._require_kb(kb_id)
        entity = self._sources.get(kb_id, site_id)
        if entity is None:
            raise NotFoundError(f"site not found: {site_id}")
        return SourceSiteOut.model_validate(entity)

    def create_source(self, kb_id: int, payload: SourceSiteCreate) -> SourceSiteOut:
        self._require_kb(kb_id)

        existing_any = self._session.get(SourceSite, payload.site_id)
        if existing_any is not None and existing_any.deleted_at is None:
            raise ValidationAppError(f"site_id already exists: {payload.site_id}")

        if existing_any is not None and existing_any.deleted_at is not None:
            # Revive soft-deleted row under the target kb
            existing_any.deleted_at = None
            existing_any.kb_id = kb_id
            existing_any.name = payload.name
            existing_any.region = payload.region.value
            existing_any.category = payload.category.value
            existing_any.entry_url = payload.entry_url
            existing_any.crawl_mode = payload.crawl_mode.value
            existing_any.allowed_domains = payload.allowed_domains
            existing_any.rate_limit_qps = payload.rate_limit_qps
            existing_any.status = (
                payload.status.value if payload.status else "pending_url"
            )
            existing_any.notes = payload.notes
            existing_any.last_probe_at = None
            existing_any.last_probe_status = None
            self._session.flush()
            return SourceSiteOut.model_validate(existing_any)

        entity = SourceSite(
            site_id=payload.site_id,
            kb_id=kb_id,
            name=payload.name,
            region=payload.region.value,
            category=payload.category.value,
            entry_url=payload.entry_url,
            crawl_mode=payload.crawl_mode.value,
            allowed_domains=payload.allowed_domains,
            rate_limit_qps=payload.rate_limit_qps,
            status=payload.status.value if payload.status else "pending_url",
            notes=payload.notes,
        )
        self._sources.add(entity)
        return SourceSiteOut.model_validate(entity)

    def update_source(
        self, kb_id: int, site_id: str, payload: SourceSiteUpdate
    ) -> SourceSiteOut:
        self._require_kb(kb_id)
        entity = self._sources.get(kb_id, site_id)
        if entity is None:
            raise NotFoundError(f"site not found: {site_id}")

        data = payload.model_dump(exclude_unset=True)
        if "entry_url" in data:
            entity.entry_url = data.pop("entry_url")
            if not entity.entry_url and data.get("status") is None:
                entity.status = "pending_url"
        for key, value in data.items():
            if hasattr(value, "value"):
                setattr(entity, key, value.value)
            else:
                setattr(entity, key, value)

        self._session.flush()
        return SourceSiteOut.model_validate(entity)

    def delete_source(self, kb_id: int, site_id: str) -> None:
        self._require_kb(kb_id)
        entity = self._sources.get(kb_id, site_id)
        if entity is None:
            raise NotFoundError(f"site not found: {site_id}")
        self._sources.soft_delete(entity)

    def probe(self, kb_id: int, payload: ProbeRequest) -> ProbeResponse:
        self._require_kb(kb_id)
        if payload.site_ids:
            entities: list[SourceSite] = []
            for sid in payload.site_ids:
                entity = self._sources.get(kb_id, sid)
                if entity is None:
                    raise NotFoundError(f"site not found: {sid}")
                entities.append(entity)
        else:
            entities = self._sources.list(kb_id)

        results: list[ProbeResultItem] = []
        for entity in entities:
            site_status, probe_status = probe_site(entity, self._settings)
            apply_probe_result(entity, site_status, probe_status)
            results.append(
                ProbeResultItem(
                    site_id=entity.site_id,
                    name=entity.name,
                    status=entity.status,
                    last_probe_status=entity.last_probe_status,
                    last_probe_at=entity.last_probe_at,
                )
            )
        self._session.flush()
        return ProbeResponse(results=results)

    def _require_kb(self, kb_id: int) -> None:
        if self._kbs.get(kb_id) is None:
            raise NotFoundError(f"knowledge base not found: {kb_id}")
