"""Shared LLM / Embedding value types."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(slots=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(slots=True)
class CallMeta:
    """Audit context passed through the gateway."""

    request_id: str = ""
    app_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    capability: str = "rag"


@dataclass(slots=True)
class ChatResult:
    content: str
    model: str
    profile_id: str
    provider: str
    usage: Usage = field(default_factory=Usage)
    raw: Mapping[str, Any] | None = None
