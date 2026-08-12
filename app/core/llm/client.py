"""LLMClient — 与文档附录示例对齐的轻量对话门面。"""

from collections.abc import Iterator

from app.core.llm.gateway import LlmGateway
from app.core.llm.types import CallMeta, ChatMessage, ChatResult
from app.web.config import Settings, get_settings


class LLMClient:
    """围绕 LlmGateway 的对话便捷封装。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        default_profile_id: str = "rag_chat",
    ) -> None:
        """初始化客户端。

        Args:
            settings: 应用配置；省略时从全局 ``get_settings()`` 读取。
            default_profile_id: 默认 chat profile ID。
        """
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
        """发起非流式对话请求。

        Args:
            messages: 对话消息列表。
            profile_id: 可选 profile 覆盖；省略时使用默认 profile。
            meta: 审计上下文，透传给网关。

        Returns:
            模型回复及用量等元信息。
        """
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
        """发起流式对话请求，逐块产出文本片段。

        Args:
            messages: 对话消息列表。
            profile_id: 可选 profile 覆盖；省略时使用默认 profile。
            meta: 审计上下文，透传给网关。

        Yields:
            模型生成的文本增量片段。
        """
        return self._gateway.chat_stream(
            messages,
            profile_id or self._default_profile_id,
            meta,
        )
