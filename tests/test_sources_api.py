"""API tests for sources CRUD + probe."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dao.database import get_session_factory, init_db, reset_engine
from app.dao.models.knowledge_base import KnowledgeBase
from app.web.config import get_settings
from app.web.main import create_app

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def client(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("CRAWL_STORAGE_DIR", str(tmp_path / "crawl"))
    get_settings.cache_clear()
    reset_engine()
    init_db()

    session = get_session_factory()()
    session.add(
        KnowledgeBase(
            id=1,
            name="农药登记评审资料",
            description="test kb",
            embedding_model="test-emb",
            embedding_dim=2048,
            status=1,
        )
    )
    session.commit()
    session.close()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()


def test_unauthorized(client: TestClient) -> None:
    resp = client.get("/api/v1/rag/kb/1/sources")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


def test_create_list_get_patch_delete(client: TestClient) -> None:
    create = client.post(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        json={
            "site_id": "us_ppis",
            "name": "美国 PPIS",
            "region": "US",
            "category": "registration",
            "entry_url": "https://example.com/ppis",
            "crawl_mode": "connector",
            "allowed_domains": ["example.com"],
            "notes": "seed",
        },
    )
    assert create.status_code == 200
    body = create.json()
    assert body["code"] == 0
    assert body["data"]["site_id"] == "us_ppis"
    assert body["data"]["status"] == "active"

    pending = client.post(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        json={
            "site_id": "cn_pending",
            "name": "待补链站点",
            "region": "CN",
            "category": "registration",
            "crawl_mode": "manual",
            "allowed_domains": [],
        },
    )
    assert pending.json()["data"]["status"] == "pending_url"

    listed = client.get(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        params={"region": "US"},
    )
    assert listed.json()["data"]["total"] == 1

    detail = client.get("/api/v1/rag/kb/1/sources/us_ppis", headers=AUTH)
    assert detail.json()["data"]["name"] == "美国 PPIS"

    patched = client.patch(
        "/api/v1/rag/kb/1/sources/us_ppis",
        headers=AUTH,
        json={"status": "disabled"},
    )
    assert patched.json()["data"]["status"] == "disabled"

    deleted = client.delete("/api/v1/rag/kb/1/sources/us_ppis", headers=AUTH)
    assert deleted.json()["data"]["deleted"] is True

    missing = client.get("/api/v1/rag/kb/1/sources/us_ppis", headers=AUTH)
    assert missing.json()["code"] == 404


def test_probe_updates_status(client: TestClient) -> None:
    client.post(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        json={
            "site_id": "ppdb",
            "name": "PPDB",
            "region": "INT",
            "category": "database",
            "entry_url": "https://example.com/ppdb",
            "crawl_mode": "connector",
            "allowed_domains": ["example.com"],
        },
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("app.rag.loader.probe.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.head.return_value = mock_resp
        resp = client.post(
            "/api/v1/rag/kb/1/sources/probe",
            headers=AUTH,
            json={"site_ids": ["ppdb"]},
        )

    assert resp.json()["code"] == 0
    result = resp.json()["data"]["results"][0]
    assert result["last_probe_status"] == "200"
    assert result["status"] == "active"


def test_sync_fetch_preview(client: TestClient) -> None:
    client.post(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        json={
            "site_id": "eu_efsa",
            "name": "EFSA",
            "region": "EU",
            "category": "evaluation",
            "entry_url": "https://example.com/efsa",
            "crawl_mode": "list_harvest",
            "allowed_domains": ["example.com"],
        },
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/efsa"
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.encoding = "utf-8"
    mock_resp.content = b"<html><body>efsa body</body></html>"

    with patch("app.rag.loader.sync_crawl.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_resp
        resp = client.post("/api/v1/rag/kb/1/sources/eu_efsa/sync", headers=AUTH)

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["saved_to_disk"] is True
    assert body["data"]["persisted_db"] is False
    assert body["data"]["item"]["ok"] is True
    assert body["data"]["item"]["storage_dir"]
    assert Path(body["data"]["item"]["storage_dir"]).is_dir()


def test_sync_batch_endpoint(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CRAWL_STORAGE_DIR", str(tmp_path / "crawl_batch"))
    get_settings.cache_clear()

    client.post(
        "/api/v1/rag/kb/1/sources",
        headers=AUTH,
        json={
            "site_id": "batch_a",
            "name": "Batch A",
            "region": "INT",
            "category": "database",
            "entry_url": "https://example.com/a",
            "crawl_mode": "single_page",
            "allowed_domains": ["example.com"],
        },
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/a"
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.encoding = "utf-8"
    mock_resp.content = b"<html><body>batch</body></html>"

    with patch("app.rag.loader.sync_crawl.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_resp
        resp = client.post(
            "/api/v1/rag/kb/1/sources/sync",
            headers=AUTH,
            params={"site_id": "batch_a"},
        )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["saved_to_disk"] is True
    assert data["items"][0]["site_id"] == "batch_a"
