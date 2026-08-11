"""Tests for chat completions API (SSE)."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.dao.database import init_db, reset_engine
from app.web.config import get_settings
from app.web.main import create_app

AUTH = {"Authorization": "Bearer test-token"}
_ADAPTER = "app.core.llm.adapters.openai_compatible.httpx.Client"


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test_chat.db"
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "qwen-plus")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-v4")
    monkeypatch.setenv("EMBEDDING_DIM", "4")
    get_settings.cache_clear()
    reset_engine()
    init_db()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    get_settings.cache_clear()


def test_chat_completions_json(
        client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert body["stream"] is False
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(
            200,
            json={
                "model": "qwen-plus",
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        )

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(_ADAPTER, client_factory)

    res = client.post(
        "/api/v1/core/llm/chat/completions",
        headers=AUTH,
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["code"] == 0
    assert payload["data"]["content"] == "hello"


def test_chat_completions_sse(
        client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"stream":true' in request.content
        lines = [
            b'data: {"choices":[{"delta":{"content":"A"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"B"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]
        return httpx.Response(200, content=b"".join(lines))

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs = dict(kwargs)
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(_ADAPTER, client_factory)

    with client.stream(
            "POST",
            "/api/v1/core/llm/chat/completions",
            headers=AUTH,
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
    ) as res:
        assert res.status_code == 200
        text = "".join(res.iter_text())
    assert '"type": "token"' in text or '"type":"token"' in text
    assert "A" in text and "B" in text
    assert '"type": "done"' in text or '"type":"done"' in text
