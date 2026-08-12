"""RAG knowledge base API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dto import ok
from app.dao.database import get_db
from app.service.kb_service import KnowledgeBaseService
from app.service.schemas.kb import KnowledgeBaseCreate
from app.web.middleware.auth import require_business_user

router = APIRouter(
    prefix="/api/v1/rag/kb",
    tags=["rag-kb"],
    dependencies=[Depends(require_business_user)],
)


def _service(db: Session = Depends(get_db)) -> KnowledgeBaseService:
    return KnowledgeBaseService(db)


@router.get("")
def list_kbs(service: KnowledgeBaseService = Depends(_service)) -> dict:
    data = service.list_kbs()
    return ok(data.model_dump(mode="json"))


@router.post("")
def create_kb(
    payload: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(_service),
) -> dict:
    data = service.create_kb(payload)
    return ok(data.model_dump(mode="json"))


@router.post("/ensure-default")
def ensure_default_kb(service: KnowledgeBaseService = Depends(_service)) -> dict:
    data = service.ensure_default_kb()
    return ok(data.model_dump(mode="json"))
