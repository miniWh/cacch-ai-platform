"""Thin facade matching docs appendix examples."""

from collections.abc import Iterator

from app.core.llm.gateway import LlmGateway
from app.core.llm.types import CallMeta, ChatMessage, ChatResult
from app.web.config import Settings, get_settings


class LLMClient:
    """Convenience wrapper around LlmGateway for chat."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        default_profile_id: str = "rag_chat",
    ) -> None:
        self._settings = settings or get_settings()
        self._gateway = LlmGateway(self._settings)
        self._default_profile_id = default_profile_id

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        profile_id: str | None = None,
        meta: CallMeta | None = None,
    ) -> ChatResult:
        return self._gateway.chat(
            messages,
            profile_id or self._default_profile_id,
            meta,
        )

    def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        profile_id: str | None = None,
        meta: CallMeta | None = None,
    ) -> Iterator[str]:
        return self._gateway.chat_stream(
            messages,
            profile_id or self._default_profile_id,
            meta,
        )
