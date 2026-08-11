"""API tests for knowledge base bootstrap."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.dao.database import init_db, reset_engine
from app.web.config import get_settings
from app.web.main import create_app

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def client(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test_kb.db"
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    get_settings.cache_clear()
    reset_engine()
    init_db()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()


def test_ensure_default_kb(client: TestClient) -> None:
    first = client.post("/api/v1/rag/kb/ensure-default", headers=AUTH)
    assert first.status_code == 200
    assert first.json()["code"] == 0
    kb_id = first.json()["data"]["id"]

    second = client.post("/api/v1/rag/kb/ensure-default", headers=AUTH)
    assert second.json()["data"]["id"] == kb_id

    listed = client.get("/api/v1/rag/kb", headers=AUTH)
    assert listed.json()["data"]["total"] >= 1
