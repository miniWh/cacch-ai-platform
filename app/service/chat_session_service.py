"""Chat session service."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationAppError
from app.common.timeutil import now_app
from app.dao.models.chat_session import ChatMessage, ChatSession
from app.dao.repositories.chat_session_repository import ChatSessionRepository
from app.dao.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.service.schemas.chat_session import (
    ChatMessageCreate,
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionDetailOut,
    ChatSessionListOut,
    ChatSessionOut,
    ChatSessionUpdate,
)

_MAX_PINNED = 10


def _new_session_id() -> str:
    return f"s_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def _new_message_id(role: str) -> str:
    prefix = {"user": "u", "assistant": "a", "system": "sys"}.get(role, "m")
    return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


class ChatSessionService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ChatSessionRepository(session)
        self._kb_repo = KnowledgeBaseRepository(session)

    def list_sessions(self, kb_id: int) -> ChatSessionListOut:
        self._require_kb(kb_id)
        items = self._repo.list_alive_by_kb(kb_id)
        return ChatSessionListOut(
            items=[ChatSessionOut.model_validate(i) for i in items],
            total=len(items),
        )

    def create_session(self, payload: ChatSessionCreate) -> ChatSessionOut:
        self._require_kb(payload.kb_id)
        entity = ChatSession(
            session_id=_new_session_id(),
            kb_id=payload.kb_id,
            app_id=payload.app_id,
            user_id=payload.user_id,
            title=payload.title.strip() or "新对话",
            title_locked=False,
            pinned=False,
            pinned_at=None,
        )
        self._repo.add_session(entity)
        self._session.commit()
        self._session.refresh(entity)
        return ChatSessionOut.model_validate(entity)

    def get_session(self, session_id: str) -> ChatSessionDetailOut:
        entity = self._require_alive(session_id)
        messages = self._repo.list_messages(session_id)
        base = ChatSessionOut.model_validate(entity)
        return ChatSessionDetailOut(
            **base.model_dump(),
            messages=[self._message_out(m) for m in messages],
        )

    def update_session(
        self, session_id: str, payload: ChatSessionUpdate
    ) -> ChatSessionOut:
        entity = self._require_alive(session_id)
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationAppError("no fields to update")

        if "title" in data and data["title"] is not None:
            title = data["title"].strip()
            if not title:
                raise ValidationAppError("title must not be empty")
            entity.title = title
            entity.title_locked = True

        if "pinned" in data and data["pinned"] is not None:
            want_pin = bool(data["pinned"])
            if want_pin and not entity.pinned:
                pinned_count = self._repo.count_pinned(entity.kb_id)
                if pinned_count >= _MAX_PINNED:
                    raise ValidationAppError(
                        f"pinned sessions limit reached ({_MAX_PINNED})"
                    )
                entity.pinned = True
                entity.pinned_at = now_app()
            elif not want_pin and entity.pinned:
                entity.pinned = False
                entity.pinned_at = None

        entity.updated_at = now_app()
        self._session.commit()
        self._session.refresh(entity)
        return ChatSessionOut.model_validate(entity)

    def delete_session(self, session_id: str) -> None:
        entity = self._require_alive(session_id)
        self._repo.soft_delete(entity)
        self._session.commit()

    def clear_sessions(self, kb_id: int) -> int:
        self._require_kb(kb_id)
        count = self._repo.soft_delete_all_by_kb(kb_id)
        self._session.commit()
        return count

    def append_message(
        self, session_id: str, payload: ChatMessageCreate
    ) -> ChatMessageOut:
        entity = self._require_alive(session_id)
        message_id = (payload.message_id or "").strip() or _new_message_id(payload.role)
        if self._repo.get_message(message_id) is not None:
            raise ValidationAppError("message_id already exists")

        msg = ChatMessage(
            message_id=message_id,
            session_id=session_id,
            role=payload.role,
            content=payload.content,
            citations_json=payload.citations,
        )
        self._repo.add_message(msg)

        # Auto-title from first user message unless user renamed
        if (
            not entity.title_locked
            and payload.role == "user"
            and entity.title in ("新对话", "")
            and payload.content.strip()
        ):
            entity.title = payload.content.strip()[:50]

        entity.updated_at = now_app()
        self._session.commit()
        self._session.refresh(msg)
        return self._message_out(msg)

    def _require_kb(self, kb_id: int) -> None:
        if self._kb_repo.get(kb_id) is None:
            raise NotFoundError(f"knowledge base {kb_id} not found")

    def _require_alive(self, session_id: str) -> ChatSession:
        entity = self._repo.get_alive(session_id)
        if entity is None:
            raise NotFoundError(f"session {session_id} not found")
        return entity

    @staticmethod
    def _message_out(msg: ChatMessage) -> ChatMessageOut:
        return ChatMessageOut(
            message_id=msg.message_id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            citations=msg.citations_json,
            created_at=msg.created_at,
        )
