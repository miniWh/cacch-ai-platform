"""Provider adapter protocol."""

from collections.abc import Iterator
from typing import Protocol

from app.core.llm.profiles import ModelProfile
from app.core.llm.types import CallMeta, ChatMessage, ChatResult


class ChatAdapter(Protocol):
    def chat(
        self,
        *,
        profile: ModelProfile,
        messages: list[ChatMessage],
        meta: CallMeta,
    ) -> ChatResult: ...

    def chat_stream(
        self,
        *,
        profile: ModelProfile,
        messages: list[ChatMessage],
        meta: CallMeta,
    ) -> Iterator[str]: ...


class EmbeddingAdapter(Protocol):
    def embed_batch(
        self,
        *,
        profile: ModelProfile,
        texts: list[str],
        meta: CallMeta,
    ) -> list[list[float]]: ...
