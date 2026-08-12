"""LLM 与 Embedding 共享的值类型。"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(slots=True)
class ChatMessage:
    """单条对话消息。"""

    role: Role
    content: str


@dataclass(slots=True)
class Usage:
    """Token 用量统计。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class CallMeta:
    """贯穿网关的审计上下文。"""

    request_id: str = ""
    app_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    capability: str = "rag"


@dataclass(slots=True)
class ChatResult:
    """非流式对话的完整返回结果。"""

    content: str
    model: str
    profile_id: str
    provider: str
    usage: Usage = field(default_factory=Usage)
    raw: Mapping[str, Any] | None = None
