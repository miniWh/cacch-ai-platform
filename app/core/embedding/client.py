"""EmbeddingClient — 通过 LlmGateway 批量生成文本向量。"""

from app.core.llm.gateway import LlmGateway
from app.core.llm.types import CallMeta
from app.web.config import Settings, get_settings


class EmbeddingClient:
    """文本向量化客户端，封装网关调用与默认 profile 配置。"""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        default_profile_id: str = "embed_default",
    ) -> None:
        """初始化客户端。

        Args:
            settings: 应用配置；省略时从全局 ``get_settings()`` 读取。
            default_profile_id: 默认 embedding profile ID。
        """
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
        """批量将文本转换为 embedding 向量。

        Args:
            texts: 待编码的文本列表。
            profile_id: 可选 profile 覆盖；省略时使用默认 profile。
            meta: 审计上下文，透传给网关。

        Returns:
            与 ``texts`` 等长的浮点向量列表。
        """
        return self._gateway.embed_batch(
            texts,
            profile_id or self._default_profile_id,
            meta,
        )
