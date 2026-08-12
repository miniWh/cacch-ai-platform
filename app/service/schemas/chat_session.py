"""对话会话相关 Pydantic 请求/响应模型。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer


class ChatSessionCreate(BaseModel):
    """创建对话会话请求体。"""

    kb_id: int = Field(gt=0, description="所属知识库 ID")
    title: str = Field(
        default="新对话", min_length=1, max_length=128, description="会话标题"
    )
    app_id: int | None = Field(default=None, description="应用 ID")
    user_id: str | None = Field(default=None, max_length=64, description="用户标识")


class ChatSessionUpdate(BaseModel):
    """更新对话会话请求体（部分字段）。"""

    title: str | None = Field(
        default=None, min_length=1, max_length=50, description="标题"
    )
    pinned: bool | None = Field(default=None, description="是否置顶")


class ChatMessageCreate(BaseModel):
    """追加消息请求体。"""

    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=0, description="消息正文")
    message_id: str | None = Field(
        default=None, max_length=64, description="客户端指定消息 ID"
    )
    citations: list[dict[str, Any]] | None = Field(default=None, description="引用片段")


class ChatMessageOut(BaseModel):
    """单条消息输出。"""

    message_id: str
    session_id: str
    role: str
    content: str
    citations: list[Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at", when_used="json")
    def _serialize_dt(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted is not None else None


class ChatSessionOut(BaseModel):
    """对话会话摘要输出。"""

    session_id: str
    kb_id: int
    app_id: int | None
    user_id: str | None
    title: str
    title_locked: bool
    pinned: bool
    pinned_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("pinned_at", "created_at", "updated_at", when_used="json")
    def _serialize_dt(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted is not None else None


class ChatSessionDetailOut(ChatSessionOut):
    """对话会话详情（含消息列表）。"""

    messages: list[ChatMessageOut] = Field(default_factory=list)


class ChatSessionListOut(BaseModel):
    """对话会话列表响应。"""

    items: list[ChatSessionOut]
    total: int
