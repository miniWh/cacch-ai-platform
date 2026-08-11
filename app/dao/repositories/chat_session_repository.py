"""Chat session / message repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.timeutil import now_app
from app.dao.models.chat_session import ChatMessage, ChatSession


class ChatSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_alive(self, session_id: str) -> ChatSession | None:
        return self._session.scalar(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.deleted_at.is_(None),
            )
        )

    def list_alive_by_kb(self, kb_id: int) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(
                ChatSession.kb_id == kb_id,
                ChatSession.deleted_at.is_(None),
            )
            .order_by(
                ChatSession.pinned.desc(),
                ChatSession.pinned_at.desc().nulls_last(),
                ChatSession.updated_at.desc(),
            )
        )
        return list(self._session.scalars(stmt))

    def count_pinned(self, kb_id: int) -> int:
        rows = self._session.scalars(
            select(ChatSession).where(
                ChatSession.kb_id == kb_id,
                ChatSession.deleted_at.is_(None),
                ChatSession.pinned.is_(True),
            )
        )
        return len(list(rows))

    def add_session(self, entity: ChatSession) -> ChatSession:
        self._session.add(entity)
        self._session.flush()
        return entity

    def soft_delete(self, entity: ChatSession) -> None:
        entity.deleted_at = now_app()
        self._session.flush()

    def soft_delete_all_by_kb(self, kb_id: int) -> int:
        items = self.list_alive_by_kb(kb_id)
        for item in items:
            item.deleted_at = now_app()
        self._session.flush()
        return len(items)

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(self._session.scalars(stmt))

    def add_message(self, entity: ChatMessage) -> ChatMessage:
        self._session.add(entity)
        self._session.flush()
        return entity

    def get_message(self, message_id: str) -> ChatMessage | None:
        return self._session.get(ChatMessage, message_id)
