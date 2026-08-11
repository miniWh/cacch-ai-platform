"""Model profile definitions (MVP: built from env settings)."""

from dataclasses import dataclass
from typing import Literal

from app.core.llm.errors import LlmConfigError
from app.web.config import Settings

ProviderName = Literal["doubao"]
ProfileKind = Literal["chat", "embedding"]


@dataclass(frozen=True, slots=True)
class ModelProfile:
    profile_id: str
    provider: ProviderName
    kind: ProfileKind
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.2
    max_tokens: int | None = None
    timeout_seconds: float = 60.0
    embedding_dim: int | None = None
    fallback_profile_id: str | None = None


def _require(value: str, name: str) -> str:
    text = value.strip()
    if not text:
        raise LlmConfigError(f"{name} is required for Doubao profiles")
    return text


def build_profiles(settings: Settings) -> dict[str, ModelProfile]:
    """Static MVP profiles: rag_chat / default_chat / embed_default."""
    api_key = _require(settings.llm_api_key, "LLM_API_KEY")
    base_url = settings.llm_base_url.rstrip("/")
    chat_model = _require(settings.llm_model, "LLM_MODEL")

    embed_key = (settings.embedding_api_key or settings.llm_api_key).strip()
    if not embed_key:
        raise LlmConfigError("EMBEDDING_API_KEY or LLM_API_KEY is required")
    embed_base = (settings.embedding_base_url or settings.llm_base_url).rstrip("/")
    embed_model = _require(settings.embedding_model, "EMBEDDING_MODEL")

    chat = ModelProfile(
        profile_id="rag_chat",
        provider="doubao",
        kind="chat",
        model=chat_model,
        api_key=api_key,
        base_url=base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
        fallback_profile_id=settings.llm_fallback_profile_id or None,
    )
    embed = ModelProfile(
        profile_id="embed_default",
        provider="doubao",
        kind="embedding",
        model=embed_model,
        api_key=embed_key,
        base_url=embed_base,
        timeout_seconds=settings.embedding_timeout_seconds,
        embedding_dim=settings.embedding_dim,
    )

    profiles = {
        chat.profile_id: chat,
        "default_chat": chat,
        embed.profile_id: embed,
    }

    if settings.llm_fallback_profile_id and settings.llm_fallback_model:
        fb_id = settings.llm_fallback_profile_id
        profiles[fb_id] = ModelProfile(
            profile_id=fb_id,
            provider="doubao",
            kind="chat",
            model=settings.llm_fallback_model,
            api_key=api_key,
            base_url=base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return profiles


def get_profile(settings: Settings, profile_id: str) -> ModelProfile:
    profiles = build_profiles(settings)
    if profile_id not in profiles:
        raise LlmConfigError(f"unknown model profile: {profile_id}")
    return profiles[profile_id]
