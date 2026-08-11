"""API tests for chat sessions (rename / pin / delete)."""

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
    db_path = tmp_path / "test_sessions.db"
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


def _kb_id(client: TestClient) -> int:
    resp = client.post("/api/v1/rag/kb/ensure-default", headers=AUTH)
    assert resp.status_code == 200
    return int(resp.json()["data"]["id"])


def test_session_crud_rename_pin_delete(client: TestClient) -> None:
    kb_id = _kb_id(client)

    created = client.post(
        "/api/v1/rag/sessions",
        headers=AUTH,
        json={"kb_id": kb_id, "title": "新对话"},
    )
    assert created.status_code == 200
    assert created.json()["code"] == 0
    session_id = created.json()["data"]["session_id"]
    assert created.json()["data"]["pinned"] is False

    listed = client.get("/api/v1/rag/sessions", headers=AUTH, params={"kb_id": kb_id})
    assert listed.json()["data"]["total"] == 1

    renamed = client.patch(
        f"/api/v1/rag/sessions/{session_id}",
        headers=AUTH,
        json={"title": "农药登记问答"},
    )
    assert renamed.json()["data"]["title"] == "农药登记问答"
    assert renamed.json()["data"]["title_locked"] is True

    pinned = client.patch(
        f"/api/v1/rag/sessions/{session_id}",
        headers=AUTH,
        json={"pinned": True},
    )
    assert pinned.json()["data"]["pinned"] is True
    assert pinned.json()["data"]["pinned_at"] is not None

    msg = client.post(
        f"/api/v1/rag/sessions/{session_id}/messages",
        headers=AUTH,
        json={"role": "user", "content": "首条消息不应覆盖已重命名标题"},
    )
    assert msg.json()["code"] == 0
    detail = client.get(f"/api/v1/rag/sessions/{session_id}", headers=AUTH)
    assert detail.json()["data"]["title"] == "农药登记问答"
    assert len(detail.json()["data"]["messages"]) == 1

    deleted = client.delete(f"/api/v1/rag/sessions/{session_id}", headers=AUTH)
    assert deleted.json()["code"] == 0
    listed2 = client.get("/api/v1/rag/sessions", headers=AUTH, params={"kb_id": kb_id})
    assert listed2.json()["data"]["total"] == 0


def test_pinned_sort_and_clear(client: TestClient) -> None:
    kb_id = _kb_id(client)
    ids: list[str] = []
    for title in ("A", "B", "C"):
        resp = client.post(
            "/api/v1/rag/sessions",
            headers=AUTH,
            json={"kb_id": kb_id, "title": title},
        )
        ids.append(resp.json()["data"]["session_id"])

    client.patch(
        f"/api/v1/rag/sessions/{ids[1]}",
        headers=AUTH,
        json={"pinned": True},
    )
    listed = client.get("/api/v1/rag/sessions", headers=AUTH, params={"kb_id": kb_id})
    items = listed.json()["data"]["items"]
    assert items[0]["session_id"] == ids[1]
    assert items[0]["pinned"] is True

    cleared = client.delete(
        "/api/v1/rag/sessions", headers=AUTH, params={"kb_id": kb_id}
    )
    assert cleared.json()["data"]["deleted"] == 3
    listed2 = client.get("/api/v1/rag/sessions", headers=AUTH, params={"kb_id": kb_id})
    assert listed2.json()["data"]["total"] == 0


def test_auto_title_from_first_user_message(client: TestClient) -> None:
    kb_id = _kb_id(client)
    created = client.post(
        "/api/v1/rag/sessions",
        headers=AUTH,
        json={"kb_id": kb_id},
    )
    session_id = created.json()["data"]["session_id"]
    client.post(
        f"/api/v1/rag/sessions/{session_id}/messages",
        headers=AUTH,
        json={"role": "user", "content": "美国EPA登记要求是什么"},
    )
    detail = client.get(f"/api/v1/rag/sessions/{session_id}", headers=AUTH)
    assert detail.json()["data"]["title"] == "美国EPA登记要求是什么"
    assert detail.json()["data"]["title_locked"] is False
