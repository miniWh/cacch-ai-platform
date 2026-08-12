"""知识库业务服务。"""

from sqlalchemy.orm import Session

from app.dao.models.knowledge_base import KnowledgeBase
from app.dao.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.service.schemas.kb import (
    KnowledgeBaseCreate,
    KnowledgeBaseListOut,
    KnowledgeBaseOut,
)
from app.web.config import Settings, get_settings


class KnowledgeBaseService:
    """知识库 CRUD 与默认库引导。"""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._repo = KnowledgeBaseRepository(session)
        self._settings = settings or get_settings()

    def list_kbs(self) -> KnowledgeBaseListOut:
        """列出全部知识库。"""
        items = self._repo.list_all()
        return KnowledgeBaseListOut(
            items=[KnowledgeBaseOut.model_validate(i) for i in items],
            total=len(items),
        )

    def create_kb(self, payload: KnowledgeBaseCreate) -> KnowledgeBaseOut:
        """创建知识库。"""
        entity = KnowledgeBase(
            name=payload.name,
            description=payload.description,
            embedding_model=payload.embedding_model,
            embedding_dim=payload.embedding_dim,
            status=payload.status,
        )
        self._repo.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return KnowledgeBaseOut.model_validate(entity)

    def ensure_default_kb(self) -> KnowledgeBaseOut:
        """幂等确保存在默认知识库，供站点等资源 API 绑定 kb_id。"""
        existing = self._repo.list_all()
        if existing:
            return KnowledgeBaseOut.model_validate(existing[0])
        return self.create_kb(
            KnowledgeBaseCreate(
                name=self._settings.default_kb_name,
                description="平台默认知识库（站点清单等资源归属）",
                embedding_model=self._settings.default_kb_embedding_model,
                embedding_dim=self._settings.default_kb_embedding_dim,
                status=1,
            )
        )
