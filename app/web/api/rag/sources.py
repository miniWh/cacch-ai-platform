"""RAG sources API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.dto import ok
from app.common.exceptions import AppError
from app.dao.database import get_db
from app.service.schemas.source import ProbeRequest, SourceSiteCreate, SourceSiteUpdate
from app.service.source_service import SourceService
from app.web.middleware.auth import require_bearer

router = APIRouter(
    prefix="/api/v1/rag/kb/{kb_id}/sources",
    tags=["rag-sources"],
    dependencies=[Depends(require_bearer)],
)


def _service(db: Session = Depends(get_db)) -> SourceService:
    return SourceService(db)


@router.get("")
def list_sources(
        kb_id: int,
        keyword: str | None = Query(default=None),
        region: str | None = Query(default=None),
        category: str | None = Query(default=None),
        status: str | None = Query(default=None),
        service: SourceService = Depends(_service),
) -> dict:
    data = service.list_sources(
        kb_id,
        keyword=keyword,
        region=region,
        category=category,
        status=status,
    )
    return ok(data.model_dump(mode="json"))


@router.post("")
def create_source(
        kb_id: int,
        payload: SourceSiteCreate,
        service: SourceService = Depends(_service),
) -> dict:
    data = service.create_source(kb_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/probe")
def probe_sources(
        kb_id: int,
        payload: ProbeRequest | None = None,
        service: SourceService = Depends(_service),
) -> dict:
    data = service.probe(kb_id, payload or ProbeRequest())
    return ok(data.model_dump(mode="json"))


@router.post("/{site_id}/sync")
def sync_source(kb_id: int, site_id: str) -> dict:
    """P1 placeholder — automated harvest/connector not implemented yet."""
    _ = (kb_id, site_id)
    raise AppError("site sync is not implemented yet (P1)", code=501)


@router.get("/{site_id}")
def get_source(
        kb_id: int,
        site_id: str,
        service: SourceService = Depends(_service),
) -> dict:
    data = service.get_source(kb_id, site_id)
    return ok(data.model_dump(mode="json"))


@router.patch("/{site_id}")
def update_source(
        kb_id: int,
        site_id: str,
        payload: SourceSiteUpdate,
        service: SourceService = Depends(_service),
) -> dict:
    data = service.update_source(kb_id, site_id, payload)
    return ok(data.model_dump(mode="json"))


@router.delete("/{site_id}")
def delete_source(
        kb_id: int,
        site_id: str,
        service: SourceService = Depends(_service),
) -> dict:
    service.delete_source(kb_id, site_id)
    return ok({"site_id": site_id, "deleted": True})
