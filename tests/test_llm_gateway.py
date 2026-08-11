"""Unit tests for Doubao LLM gateway (httpx mocked)."""

from __future__ import annotations

import json

import httpx
import pytest

from app.core.llm.errors import LlmProviderError
from app.core.llm.gateway import LlmGateway
from app.core.llm.types import CallMeta, ChatMessage
from app.web.config import Settings


def _settings(**kwargs: object) -> Settings:
    base = {
        "llm_api_key": "test-key",
        "llm_base_url": "https://ark.example.com/api/v3",
        "llm_model": "ep-chat-test",
        "embedding_model": "ep-embed-test",
        "embedding_dim": 4,
    }
    base.update(kwargs)
    return Settings(**base)  # type: ignore[arg-type]


def test_chat_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        body = json.loads(request.content.decode())
        assert body["model"] == "ep-chat-test"
        assert body["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "ep-chat-test",
                "choices": [{"message": {"role": "assistant", "content": "你好"}}],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.core.llm.adapters.doubao.httpx.Client", client_factory)

    gw = LlmGateway(_settings())
    result = gw.chat(
        [ChatMessage(role="user", content="hi")],
        "rag_chat",
        CallMeta(request_id="t1", capability="test"),
    )
    assert result.content == "你好"
    assert result.usage.total_tokens == 5
    assert result.provider == "doubao"


def test_chat_stream_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream":true' in request.content
        lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"!"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]
        return httpx.Response(200, content=b"".join(lines))

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.core.llm.adapters.doubao.httpx.Client", client_factory)

    gw = LlmGateway(_settings())
    text = "".join(
        gw.chat_stream(
            [ChatMessage(role="user", content="hi")],
            "default_chat",
        )
    )
    assert text == "Hello!"


def test_embed_batch_validates_dim(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.3, 0.4, 0.5, 0.6]},
                    {"index": 0, "embedding": [0.1, 0.2, 0.3, 0.4]},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.core.llm.adapters.doubao.httpx.Client", client_factory)

    gw = LlmGateway(_settings())
    vectors = gw.embed_batch(["a", "b"])
    assert vectors[0][0] == pytest.approx(0.1)
    assert vectors[1][0] == pytest.approx(0.3)


def test_embed_dim_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.1, 0.2]}]},
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.core.llm.adapters.doubao.httpx.Client", client_factory)

    gw = LlmGateway(_settings(embedding_dim=4))
    with pytest.raises(LlmProviderError, match="dim mismatch"):
        gw.embed_batch(["a"])


def test_chat_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": "invalid api key"}},
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.core.llm.adapters.doubao.httpx.Client", client_factory)

    gw = LlmGateway(_settings())
    with pytest.raises(LlmProviderError, match="401"):
        gw.chat([ChatMessage(role="user", content="x")], "rag_chat")
