"""Auth / login / RBAC API tests (sqlite + fake persondetail)."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.dao.database import get_session_factory, init_db, reset_engine
from app.web.config import get_settings
from app.web.main import create_app

SERVICE = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def client(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test_auth.db"
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    get_settings.cache_clear()
    reset_engine()
    init_db()

    session = get_session_factory()()
    try:
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS persondetail (
                    "staffNo" TEXT,
                    "mobileNo" TEXT,
                    "staffName" TEXT,
                    "workEmail" TEXT,
                    "staffStatus" TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO persondetail
                ("staffNo", "mobileNo", "staffName", "workEmail", "staffStatus")
                VALUES
                ('wx001', '13800000001', '张三', 'zhang@example.com', 'IN_SERVICE'),
                ('wx002', '13800000002', '李四', NULL, 'LEAVE')
                """
            )
        )
        session.commit()
    finally:
        session.close()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()


def _bootstrap(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/bootstrap",
        headers=SERVICE,
        json={"mobile": "13800000001", "password": "Admin1234"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["code"] == 0
    return resp.json()["data"]["plain_password"]


def _login(client: TestClient, mobile: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"mobile": mobile, "password": password, "remember_today": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["code"] == 0
    return resp.json()["data"]["access_token"]


def test_bootstrap_login_force_password_and_menu(client: TestClient) -> None:
    _bootstrap(client)
    token = _login(client, "13800000001", "Admin1234")
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["data"]["must_change_password"] is True
    assert "users" in me.json()["data"]["menu_ids"]

    # must change password blocks business APIs
    blocked = client.get("/api/v1/rag/kb", headers=headers)
    assert blocked.status_code == 403

    changed = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"old_password": "Admin1234", "new_password": "NewPass123"},
    )
    assert changed.json()["code"] == 0

    token2 = _login(client, "13800000001", "NewPass123")
    headers2 = {"Authorization": f"Bearer {token2}"}
    ok_kb = client.get("/api/v1/rag/kb", headers=headers2)
    assert ok_kb.status_code == 200
    assert ok_kb.json()["code"] == 0


def test_reject_non_inservice_bootstrap(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/bootstrap",
        headers=SERVICE,
        json={"mobile": "13800000002", "password": "Admin1234"},
    )
    assert resp.json()["code"] != 0


def test_create_user_with_role_and_service_token_kb(client: TestClient) -> None:
    _bootstrap(client)
    # service token still works for automation
    listed = client.get("/api/v1/rag/kb", headers=SERVICE)
    assert listed.status_code == 200

    token = _login(client, "13800000001", "Admin1234")
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"old_password": "Admin1234", "new_password": "NewPass123"},
    )
    token = _login(client, "13800000001", "NewPass123")
    headers = {"Authorization": f"Bearer {token}"}

    roles = client.get("/api/v1/auth/roles", headers=headers).json()["data"]["items"]
    user_role = next(r for r in roles if r["code"] == "user")
    orgs = client.get("/api/v1/auth/orgs", headers=headers).json()["data"]["items"]
    org_id = orgs[0]["id"]

    # insert another HR person for create
    session = get_session_factory()()
    try:
        session.execute(
            text(
                """
                INSERT INTO persondetail
                ("staffNo", "mobileNo", "staffName", "workEmail", "staffStatus")
                VALUES ('wx003', '13800000003', '王五', NULL, 'IN_SERVICE')
                """
            )
        )
        session.commit()
    finally:
        session.close()

    created = client.post(
        "/api/v1/auth/users",
        headers=headers,
        json={
            "mobile": "13800000003",
            "org_id": org_id,
            "role_id": user_role["id"],
            "generate_password": True,
        },
    )
    assert created.json()["code"] == 0
    plain = created.json()["data"]["plain_password"]
    assert created.json()["data"]["user"]["menu_ids"] == ["chat"]

    user_token = _login(client, "13800000003", plain)
    user_headers = {"Authorization": f"Bearer {user_token}"}
    client.post(
        "/api/v1/auth/change-password",
        headers=user_headers,
        json={"old_password": plain, "new_password": "UserPass12"},
    )
    user_token = _login(client, "13800000003", "UserPass12")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    denied = client.get("/api/v1/auth/users", headers=user_headers)
    assert denied.status_code == 403
