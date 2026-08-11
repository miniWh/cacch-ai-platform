"""EmbeddingClient — batch embed via LlmGateway."""

from app.core.llm.gateway import LlmGateway
from app.core.llm.types import CallMeta
from app.web.config import Settings, get_settings


class EmbeddingClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        default_profile_id: str = "embed_default",
    ) -> None:
        self._settings = settings or get_settings()
        self._gateway = LlmGateway(self._settings)
        self._default_profile_id = default_profile_id

    def embed_batch(
        self,
        texts: list[str],
        *,
        profile_id: str | None = None,
        meta: CallMeta | None = None,
    ) -> list[list[float]]:
        return self._gateway.embed_batch(
            texts,
            profile_id or self._default_profile_id,
            meta,
        )
