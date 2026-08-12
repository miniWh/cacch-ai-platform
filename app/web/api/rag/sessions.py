"""RAG 对话会话 HTTP API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.dto import ok
from app.dao.database import get_db
from app.service.chat_session_service import ChatSessionService
from app.service.schemas.chat_session import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
)
from app.web.middleware.auth import require_business_user

router = APIRouter(
    prefix="/api/v1/rag/sessions",
    tags=["rag-sessions"],
    dependencies=[Depends(require_business_user)],
)


def _service(db: Session = Depends(get_db)) -> ChatSessionService:
    """FastAPI 依赖：构造 ChatSessionService。"""
    return ChatSessionService(db)


@router.get("")
def list_sessions(
    kb_id: int = Query(..., gt=0),
    service: ChatSessionService = Depends(_service),
) -> dict:
    """列出指定知识库下的对话会话。"""
    data = service.list_sessions(kb_id)
    return ok(data.model_dump(mode="json"))


@router.post("")
def create_session(
    payload: ChatSessionCreate,
    service: ChatSessionService = Depends(_service),
) -> dict:
    """创建新对话会话。"""
    data = service.create_session(payload)
    return ok(data.model_dump(mode="json"))


@router.delete("")
def clear_sessions(
    kb_id: int = Query(..., gt=0),
    service: ChatSessionService = Depends(_service),
) -> dict:
    """清空指定知识库下全部会话。"""
    count = service.clear_sessions(kb_id)
    return ok({"deleted": count})


@router.get("/{session_id}")
def get_session(
    session_id: str,
    service: ChatSessionService = Depends(_service),
) -> dict:
    """获取会话详情及消息列表。"""
    data = service.get_session(session_id)
    return ok(data.model_dump(mode="json"))


@router.patch("/{session_id}")
def update_session(
    session_id: str,
    payload: ChatSessionUpdate,
    service: ChatSessionService = Depends(_service),
) -> dict:
    """更新会话标题或置顶状态。"""
    data = service.update_session(session_id, payload)
    return ok(data.model_dump(mode="json"))


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    service: ChatSessionService = Depends(_service),
) -> dict:
    """删除单个对话会话。"""
    service.delete_session(session_id)
    return ok({"session_id": session_id})


@router.post("/{session_id}/messages")
def append_message(
    session_id: str,
    payload: ChatMessageCreate,
    service: ChatSessionService = Depends(_service),
) -> dict:
    """向会话追加一条消息。"""
    data = service.append_message(session_id, payload)
    return ok(data.model_dump(mode="json"))
