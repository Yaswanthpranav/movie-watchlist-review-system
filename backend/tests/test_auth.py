"""Authentication endpoint tests."""

import uuid

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.crud import user as user_crud
from app.models import User


def test_register_and_login_with_username_and_email(client: TestClient) -> None:
    """User can register (201) without exposing password_hash and log in via username or email."""
    reg_res = client.post(
        "/auth/register",
        json={
            "username": "cinephile",
            "email": "cinephile@example.com",
            "password": "myStrongPassword1",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["username"] == "cinephile"
    assert reg_data["email"] == "cinephile@example.com"
    assert "user_id" in reg_data
    assert "create_date" in reg_data
    assert "password_hash" not in reg_data
    assert "password" not in reg_data

    # Login via username
    login_res = client.post(
        "/auth/login",
        json={"username": "cinephile", "password": "myStrongPassword1"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]
    assert "password_hash" not in token_data["user"]

    # Login via email
    login_email_res = client.post(
        "/auth/login",
        json={"email": "cinephile@example.com", "password": "myStrongPassword1"},
    )
    assert login_email_res.status_code == 200
    assert login_email_res.json()["access_token"]

    # Profile check via /auth/me
    me_res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "cinephile"


def test_login_invalid_credentials_returns_401(client: TestClient) -> None:
    """Wrong password or unknown username returns 401 Unauthorized."""
    client.post(
        "/auth/register",
        json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "correctpassword",
        },
    )

    bad_pw = client.post(
        "/auth/login",
        json={"username": "validuser", "password": "wrongpassword"},
    )
    assert bad_pw.status_code == 401

    unknown_user = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "correctpassword"},
    )
    assert unknown_user.status_code == 401


def test_auth_me_requires_valid_bearer_token(client: TestClient) -> None:
    """Missing or invalid Bearer token returns 401 Unauthorized."""
    no_token = client.get("/auth/me")
    assert no_token.status_code == 401

    bad_token = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert bad_token.status_code == 401


def test_register_validation_errors_return_422(client: TestClient) -> None:
    """Invalid email, short password, and short username return 422."""
    bad_email = client.post(
        "/auth/register",
        json={"username": "user123", "email": "not-an-email", "password": "password123"},
    )
    assert bad_email.status_code == 422

    short_pw = client.post(
        "/auth/register",
        json={"username": "user123", "email": "u@example.com", "password": "123"},
    )
    assert short_pw.status_code == 422

    blank_user = client.post(
        "/auth/register",
        json={"username": "   ", "email": "u@example.com", "password": "password123"},
    )
    assert blank_user.status_code == 422


def test_login_validation_missing_identifier_returns_422(client: TestClient) -> None:
    """Login request without username or email returns 422."""
    res = client.post("/auth/login", json={"password": "somepassword"})
    assert res.status_code == 422


def test_supabase_auth_postgres_flow(
    db_session: Session,
    monkeypatch,
) -> None:
    """Verify PostgreSQL/Supabase Auth register & login flow via auth_user_id mapping."""
    auth_uid = uuid.uuid4()
    supa_settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/postgres",
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_ANON_KEY="anon-key",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
    )

    class _FakeResponse:
        def __init__(self, status_code: int, body: dict):
            self.status_code = status_code
            self._body = body
            self.content = b"{}"

        def json(self):
            return self._body

    def _fake_post(_self, url: str, headers: dict, json: dict):
        if url.endswith("/auth/v1/admin/users"):
            # Simulate live DB trigger handle_new_user() inserting into public."user"
            db_session.add(
                User(
                    username=json["user_metadata"]["username"],
                    email=json["email"],
                    auth_user_id=auth_uid,
                )
            )
            db_session.flush()
            return _FakeResponse(200, {"id": str(auth_uid), "email": json["email"]})
        if "/auth/v1/token" in url:
            if json["password"] == "rightpass123":
                return _FakeResponse(200, {"access_token": "supa-jwt"})
            return _FakeResponse(400, {"error_description": "Invalid login credentials"})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(httpx.Client, "post", _fake_post)

    created = user_crud.register_user(
        db_session,
        username="supa_alice",
        email="supa_alice@example.com",
        password="rightpass123",
        settings=supa_settings,
    )
    assert created.auth_user_id == auth_uid
    assert created.username == "supa_alice"

    authed = user_crud.authenticate_user(
        db_session,
        username="supa_alice",
        email=None,
        password="rightpass123",
        settings=supa_settings,
    )
    assert authed is not None
    assert authed.user_id == created.user_id

    failed = user_crud.authenticate_user(
        db_session,
        username=None,
        email="supa_alice@example.com",
        password="wrongpass",
        settings=supa_settings,
    )
    assert failed is None


def test_supabase_auth_headers_handles_modern_and_legacy_keys() -> None:
    """Modern sb_* keys omit Authorization: Bearer, while legacy JWT keys include both."""
    pub_headers = user_crud._supabase_auth_headers("sb_publishable_example123")
    assert pub_headers["apikey"] == "sb_publishable_example123"
    assert "Authorization" not in pub_headers

    sec_headers = user_crud._supabase_auth_headers("sb_secret_example123")
    assert sec_headers["apikey"] == "sb_secret_example123"
    assert "Authorization" not in sec_headers

    legacy_headers = user_crud._supabase_auth_headers("eyJhbGciOiJIUzI1NiJ9.payload.sig")
    assert legacy_headers["apikey"] == "eyJhbGciOiJIUzI1NiJ9.payload.sig"
    assert legacy_headers["Authorization"] == "Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
