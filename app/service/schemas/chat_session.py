"""Chat session schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer


class ChatSessionCreate(BaseModel):
    kb_id: int = Field(gt=0)
    title: str = Field(default="新对话", min_length=1, max_length=128)
    app_id: int | None = None
    user_id: str | None = Field(default=None, max_length=64)


class ChatSessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    pinned: bool | None = None


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=0)
    message_id: str | None = Field(default=None, max_length=64)
    citations: list[dict[str, Any]] | None = None


class ChatMessageOut(BaseModel):
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
    messages: list[ChatMessageOut] = Field(default_factory=list)


class ChatSessionListOut(BaseModel):
    items: list[ChatSessionOut]
    total: int
