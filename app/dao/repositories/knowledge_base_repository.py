"""Knowledge base repository (minimal for sources FK checks)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dao.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, kb_id: int) -> KnowledgeBase | None:
        return self._session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )

    def list_all(self) -> list[KnowledgeBase]:
        return list(
            self._session.scalars(
                select(KnowledgeBase).order_by(KnowledgeBase.id.asc())
            )
        )

    def get_by_name(self, name: str) -> KnowledgeBase | None:
        return self._session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )

    def add(self, entity: KnowledgeBase) -> KnowledgeBase:
        self._session.add(entity)
        self._session.flush()
        return entity
