"""OpenAI 兼容协议 LLM 适配器（阿里云百炼 / 通义千问等），基于 httpx 实现。"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx

from app.core.llm.errors import LlmProviderError
from app.core.llm.profiles import ModelProfile
from app.core.llm.types import CallMeta, ChatMessage, ChatResult, Usage

logger = logging.getLogger(__name__)


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _messages_payload(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _parse_usage(data: dict[str, Any]) -> Usage:
    usage = data.get("usage") or {}
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    total = int(usage.get("total_tokens") or (prompt + completion))
    return Usage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
    )


def _raise_http(resp: httpx.Response) -> None:
    try:
        body = resp.json()
        err = body.get("error") if isinstance(body, dict) else None
        msg = str(err.get("message") or err) if isinstance(err, dict) else resp.text
    except Exception:  # noqa: BLE001
        msg = resp.text
    raise LlmProviderError(
        f"LLM API error HTTP {resp.status_code}: {msg}",
        status_code=resp.status_code,
    )


class OpenAICompatibleChatAdapter:
    """OpenAI Chat Completions 兼容对话适配器。"""

    def chat(
        self,
        *,
        profile: ModelProfile,
        messages: list[ChatMessage],
        meta: CallMeta,
    ) -> ChatResult:
        """发起非流式 chat/completions 请求。

        Args:
            profile: 模型连接与参数配置。
            messages: 对话消息列表。
            meta: 审计上下文（当前主要用于日志关联）。

        Returns:
            解析后的模型回复与 token 用量。

        Raises:
            LlmProviderError: HTTP 错误或响应格式异常。
        """
        url = f"{profile.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": profile.model,
            "messages": _messages_payload(messages),
            "temperature": profile.temperature,
            "stream": False,
        }
        if profile.max_tokens is not None:
            payload["max_tokens"] = profile.max_tokens

        try:
            with httpx.Client(timeout=profile.timeout_seconds) as client:
                resp = client.post(
                    url, headers=_auth_headers(profile.api_key), json=payload
                )
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"chat request failed: {exc}") from exc

        if resp.status_code >= 400:
            _raise_http(resp)

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmProviderError(f"unexpected chat response: {data}") from exc

        return ChatResult(
            content=str(content or ""),
            model=str(data.get("model") or profile.model),
            profile_id=profile.profile_id,
            provider=profile.provider,
            usage=_parse_usage(data),
            raw=data,
        )

    def chat_stream(
        self,
        *,
        profile: ModelProfile,
        messages: list[ChatMessage],
        meta: CallMeta,
    ) -> Iterator[str]:
        """发起 SSE 流式 chat/completions 请求。

        Args:
            profile: 模型连接与参数配置。
            messages: 对话消息列表。
            meta: 审计上下文，无效 SSE 块会记录 request_id。

        Yields:
            模型回复的文本增量片段。

        Raises:
            LlmProviderError: HTTP 错误或网络异常。
        """
        url = f"{profile.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": profile.model,
            "messages": _messages_payload(messages),
            "temperature": profile.temperature,
            "stream": True,
        }
        if profile.max_tokens is not None:
            payload["max_tokens"] = profile.max_tokens

        try:
            with (
                httpx.Client(timeout=profile.timeout_seconds) as client,
                client.stream(
                    "POST",
                    url,
                    headers=_auth_headers(profile.api_key),
                    json=payload,
                ) as resp,
            ):
                if resp.status_code >= 400:
                    _ = resp.read()
                    _raise_http(resp)
                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning(
                            "skip invalid SSE chunk request_id=%s",
                            meta.request_id,
                        )
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield str(piece)
        except LlmProviderError:
            raise
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"chat stream failed: {exc}") from exc


class OpenAICompatibleEmbeddingAdapter:
    """OpenAI Embeddings 兼容向量化适配器。"""

    def embed_batch(
        self,
        *,
        profile: ModelProfile,
        texts: list[str],
        meta: CallMeta,
    ) -> list[list[float]]:
        """批量调用 embeddings 接口生成向量。

        Args:
            profile: 模型连接与维度等参数。
            texts: 待编码文本列表；空列表直接返回 ``[]``。
            meta: 审计上下文（预留，当前未直接使用）。

        Returns:
            与 ``texts`` 顺序一致的浮点向量列表。

        Raises:
            LlmProviderError: HTTP 错误、响应格式或维度不匹配。
        """
        if not texts:
            return []
        url = f"{profile.base_url}/embeddings"
        payload: dict[str, Any] = {"model": profile.model, "input": texts}
        # 百炼 text-embedding-v4 等支持自定义维度；不传时常见默认 1024
        if profile.embedding_dim:
            payload["dimensions"] = profile.embedding_dim
        try:
            with httpx.Client(timeout=profile.timeout_seconds) as client:
                resp = client.post(
                    url, headers=_auth_headers(profile.api_key), json=payload
                )
        except httpx.HTTPError as exc:
            raise LlmProviderError(f"embed request failed: {exc}") from exc

        if resp.status_code >= 400:
            _raise_http(resp)

        data = resp.json()
        items = data.get("data")
        if not isinstance(items, list):
            raise LlmProviderError(f"unexpected embed response: {data}")

        ordered = sorted(
            items,
            key=lambda x: int(x.get("index", 0)) if isinstance(x, dict) else 0,
        )
        vectors: list[list[float]] = []
        for item in ordered:
            if not isinstance(item, dict) or "embedding" not in item:
                raise LlmProviderError(f"missing embedding in response item: {item}")
            vec = [float(v) for v in item["embedding"]]
            if profile.embedding_dim and len(vec) != profile.embedding_dim:
                raise LlmProviderError(
                    f"embedding dim mismatch: got {len(vec)}, "
                    f"expected {profile.embedding_dim}"
                )
            vectors.append(vec)

        if len(vectors) != len(texts):
            raise LlmProviderError(
                f"embedding count mismatch: got {len(vectors)}, expected {len(texts)}"
            )
        return vectors
