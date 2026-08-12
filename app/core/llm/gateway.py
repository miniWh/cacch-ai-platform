"""LLM 网关 — profile 路由、适配器分发与基础审计日志。"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator

from app.core.llm.adapters.openai_compatible import (
    OpenAICompatibleChatAdapter,
    OpenAICompatibleEmbeddingAdapter,
)
from app.core.llm.errors import LlmConfigError, LlmError
from app.core.llm.profiles import ModelProfile, get_profile
from app.core.llm.types import CallMeta, ChatMessage, ChatResult
from app.web.config import Settings, get_settings

logger = logging.getLogger(__name__)

_CHAT = OpenAICompatibleChatAdapter()
_EMBED = OpenAICompatibleEmbeddingAdapter()


class LlmGateway:
    """统一入口：按 profile 选择模型提供商并完成调用与审计。"""

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化网关及已注册的 provider 适配器。

        Args:
            settings: 应用配置；省略时从全局 ``get_settings()`` 读取。
        """
        self._settings = settings or get_settings()
        # 当前接入：阿里云百炼 OpenAI 兼容协议（provider=qwen）
        self._chat_adapters = {"qwen": _CHAT}
        self._embed_adapters = {"qwen": _EMBED}

    def _resolve(self, profile_id: str, *, kind: str) -> ModelProfile:
        profile = get_profile(self._settings, profile_id)
        if profile.kind != kind:
            raise LlmConfigError(
                f"profile {profile_id} is kind={profile.kind}, expected {kind}"
            )
        return profile

    def chat(
        self,
        messages: list[ChatMessage],
        profile_id: str,
        meta: CallMeta | None = None,
    ) -> ChatResult:
        """非流式对话；主 profile 失败时可按配置回退到备用 profile。

        Args:
            messages: 对话消息列表。
            profile_id: 使用的 chat profile ID。
            meta: 审计上下文；省略时使用默认值。

        Returns:
            模型完整回复及用量信息。
        """
        meta = meta or CallMeta()
        profile = self._resolve(profile_id, kind="chat")
        return self._chat_with_fallback(messages, profile, meta)

    def chat_stream(
        self,
        messages: list[ChatMessage],
        profile_id: str,
        meta: CallMeta | None = None,
    ) -> Iterator[str]:
        """流式对话，逐块返回文本增量。

        Args:
            messages: 对话消息列表。
            profile_id: 使用的 chat profile ID。
            meta: 审计上下文；省略时使用默认值。

        Yields:
            模型生成的文本片段。
        """
        meta = meta or CallMeta()
        profile = self._resolve(profile_id, kind="chat")
        adapter = self._chat_adapters.get(profile.provider)
        if adapter is None:
            raise LlmConfigError(f"unsupported chat provider: {profile.provider}")

        started = time.perf_counter()
        try:
            yield from adapter.chat_stream(
                profile=profile, messages=messages, meta=meta
            )
            self._audit(
                event="llm.chat_stream",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="ok",
            )
        except LlmError as exc:
            self._audit(
                event="llm.chat_stream",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error",
                error=str(exc),
            )
            raise

    def embed_batch(
        self,
        texts: list[str],
        profile_id: str = "embed_default",
        meta: CallMeta | None = None,
    ) -> list[list[float]]:
        """批量生成文本 embedding 向量。

        Args:
            texts: 待编码文本列表。
            profile_id: embedding profile ID，默认 ``embed_default``。
            meta: 审计上下文；省略时使用 embedding 能力标识。

        Returns:
            与输入等长的向量列表。
        """
        meta = meta or CallMeta(capability="embedding")
        profile = self._resolve(profile_id, kind="embedding")
        adapter = self._embed_adapters.get(profile.provider)
        if adapter is None:
            raise LlmConfigError(f"unsupported embedding provider: {profile.provider}")

        started = time.perf_counter()
        try:
            vectors = adapter.embed_batch(profile=profile, texts=texts, meta=meta)
            self._audit(
                event="llm.embed_batch",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="ok",
                extra={"batch_size": len(texts)},
            )
            return vectors
        except LlmError as exc:
            self._audit(
                event="llm.embed_batch",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error",
                error=str(exc),
            )
            raise

    def _chat_with_fallback(
        self,
        messages: list[ChatMessage],
        profile: ModelProfile,
        meta: CallMeta,
    ) -> ChatResult:
        adapter = self._chat_adapters.get(profile.provider)
        if adapter is None:
            raise LlmConfigError(f"unsupported chat provider: {profile.provider}")

        started = time.perf_counter()
        try:
            result = adapter.chat(profile=profile, messages=messages, meta=meta)
            self._audit(
                event="llm.chat",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="ok",
                usage=result.usage,
            )
            return result
        except LlmError as first_err:
            self._audit(
                event="llm.chat",
                profile=profile,
                meta=meta,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error",
                error=str(first_err),
            )
            fb = profile.fallback_profile_id
            if not fb or fb == profile.profile_id:
                raise
            fb_profile = self._resolve(fb, kind="chat")
            fb_adapter = self._chat_adapters.get(fb_profile.provider)
            if fb_adapter is None:
                raise
            started_fb = time.perf_counter()
            try:
                result = fb_adapter.chat(
                    profile=fb_profile, messages=messages, meta=meta
                )
                self._audit(
                    event="llm.chat_fallback",
                    profile=fb_profile,
                    meta=meta,
                    latency_ms=int((time.perf_counter() - started_fb) * 1000),
                    status="ok",
                    usage=result.usage,
                    extra={"from_profile": profile.profile_id},
                )
                return result
            except LlmError as second_err:
                self._audit(
                    event="llm.chat_fallback",
                    profile=fb_profile,
                    meta=meta,
                    latency_ms=int((time.perf_counter() - started_fb) * 1000),
                    status="error",
                    error=str(second_err),
                    extra={"from_profile": profile.profile_id},
                )
                raise

    def _audit(
        self,
        *,
        event: str,
        profile: ModelProfile,
        meta: CallMeta,
        latency_ms: int,
        status: str,
        usage: object | None = None,
        error: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "event": event,
            "request_id": meta.request_id,
            "app_id": meta.app_id,
            "user_id": meta.user_id,
            "session_id": meta.session_id,
            "capability": meta.capability,
            "profile_id": profile.profile_id,
            "provider": profile.provider,
            "model": profile.model,
            "latency_ms": latency_ms,
            "status": status,
        }
        if usage is not None:
            payload["usage"] = usage
        if error:
            payload["error"] = error
        if extra:
            payload.update(extra)
        logger.info("llm_audit %s", payload)
