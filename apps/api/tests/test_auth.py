from pathlib import Path

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service, get_settings, get_user_repo
from app.main import app


def _clear_auth_caches() -> None:
    get_auth_service.cache_clear()
    get_user_repo.cache_clear()
    get_settings.cache_clear()


def test_register_login_and_me_persist(tmp_path: Path, monkeypatch) -> None:
    users_file = tmp_path / "demo_users.json"
    monkeypatch.setenv("DEMO_USERS_FILE", str(users_file))
    monkeypatch.setenv("DEMO_AUTH_SECRET", "test-secret")
    _clear_auth_caches()

    client = TestClient(app)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Boming Xi",
            "email": "boming@example.com",
            "password": "strongpass123",
        },
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["user"]["email"] == "boming@example.com"
    assert users_file.exists()

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {register_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["name"] == "Boming Xi"

    _clear_auth_caches()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "boming@example.com", "password": "strongpass123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "boming@example.com"


def test_register_rejects_duplicate_email(tmp_path: Path, monkeypatch) -> None:
    users_file = tmp_path / "demo_users.json"
    monkeypatch.setenv("DEMO_USERS_FILE", str(users_file))
    monkeypatch.setenv("DEMO_AUTH_SECRET", "test-secret")
    _clear_auth_caches()

    client = TestClient(app)

    payload = {
        "name": "Demo User",
        "email": "demo@example.com",
        "password": "strongpass123",
    }
    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 409

