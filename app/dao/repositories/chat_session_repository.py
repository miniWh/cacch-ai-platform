"""聊天会话与消息仓储。

封装对话线程及消息的查询、创建与软删除操作。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.timeutil import now_app
from app.dao.models.chat_session import ChatMessage, ChatSession


class ChatSessionRepository:
    """聊天会话仓储。

    管理 ``ChatSession`` 与 ``ChatMessage`` 的持久化读写。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_alive(self, session_id: str) -> ChatSession | None:
        """按 ID 查询未软删除的会话。"""
        return self._session.scalar(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.deleted_at.is_(None),
            )
        )

    def list_alive_by_kb(self, kb_id: int) -> list[ChatSession]:
        """列出某知识库下全部未删除会话（置顶优先，再按更新时间降序）。"""
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
        """统计某知识库下已置顶且未删除的会话数量。"""
        rows = self._session.scalars(
            select(ChatSession).where(
                ChatSession.kb_id == kb_id,
                ChatSession.deleted_at.is_(None),
                ChatSession.pinned.is_(True),
            )
        )
        return len(list(rows))

    def add_session(self, entity: ChatSession) -> ChatSession:
        """新增会话并 flush。"""
        self._session.add(entity)
        self._session.flush()
        return entity

    def soft_delete(self, entity: ChatSession) -> None:
        """软删除单个会话（设置 ``deleted_at``）。"""
        entity.deleted_at = now_app()
        self._session.flush()

    def soft_delete_all_by_kb(self, kb_id: int) -> int:
        """软删除某知识库下全部未删除会话，返回删除数量。"""
        items = self.list_alive_by_kb(kb_id)
        for item in items:
            item.deleted_at = now_app()
        self._session.flush()
        return len(items)

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        """按创建时间升序列出会话内全部消息。"""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(self._session.scalars(stmt))

    def add_message(self, entity: ChatMessage) -> ChatMessage:
        """新增消息并 flush。"""
        self._session.add(entity)
        self._session.flush()
        return entity

    def get_message(self, message_id: str) -> ChatMessage | None:
        """按消息 ID 查询。"""
        return self._session.get(ChatMessage, message_id)
