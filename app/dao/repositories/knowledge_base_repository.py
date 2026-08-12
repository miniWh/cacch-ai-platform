"""知识库仓储。

提供知识库的基本查询与创建，主要用于外键校验及列表展示。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dao.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    """知识库仓储。

    封装 ``KnowledgeBase`` 实体的查询与新增操作。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, kb_id: int) -> KnowledgeBase | None:
        """按主键查询知识库。"""
        return self._session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )

    def list_all(self) -> list[KnowledgeBase]:
        """按 ID 升序列出全部知识库。"""
        return list(
            self._session.scalars(
                select(KnowledgeBase).order_by(KnowledgeBase.id.asc())
            )
        )

    def get_by_name(self, name: str) -> KnowledgeBase | None:
        """按名称精确查询知识库。"""
        return self._session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )

    def add(self, entity: KnowledgeBase) -> KnowledgeBase:
        """新增知识库并 flush 以获取自增 ID。"""
        self._session.add(entity)
        self._session.flush()
        return entity
