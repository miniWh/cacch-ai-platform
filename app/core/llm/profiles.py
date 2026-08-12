"""模型 Profile 定义（MVP：由环境配置构建）。"""

from dataclasses import dataclass
from typing import Literal, cast

from app.core.llm.errors import LlmConfigError
from app.web.config import Settings

ProviderName = Literal["qwen"]
ProfileKind = Literal["chat", "embedding"]
SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"qwen"})


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """单次 LLM/Embedding 调用所需的模型与连接参数。"""

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
        raise LlmConfigError(f"{name} is required for LLM profiles")
    return text


def _provider(settings: Settings) -> ProviderName:
    name = settings.llm_provider.strip().lower()
    if name not in SUPPORTED_PROVIDERS:
        raise LlmConfigError(
            f"unsupported LLM_PROVIDER={settings.llm_provider!r}; "
            f"supported={sorted(SUPPORTED_PROVIDERS)}"
        )
    return cast(ProviderName, name)


def build_profiles(settings: Settings) -> dict[str, ModelProfile]:
    """从应用配置构建静态 MVP profile 集合。

    默认包含 ``rag_chat`` / ``default_chat`` / ``embed_default``，
    若配置了备用模型则额外注册 fallback profile。

    Args:
        settings: 应用配置对象。

    Returns:
        profile_id 到 ``ModelProfile`` 的映射。
    """
    provider = _provider(settings)
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
        provider=provider,
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
        provider=provider,
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
            provider=provider,
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
    """按 ID 获取 profile，不存在时抛出配置错误。

    Args:
        settings: 应用配置对象。
        profile_id: profile 标识符。

    Returns:
        对应的 ``ModelProfile`` 实例。

    Raises:
        LlmConfigError: profile_id 未知或配置不完整。
    """
    profiles = build_profiles(settings)
    if profile_id not in profiles:
        raise LlmConfigError(f"unknown model profile: {profile_id}")
    return profiles[profile_id]
