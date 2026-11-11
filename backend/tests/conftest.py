"""Pytest fixtures providing isolated transactional DB sessions and FastAPI TestClient.

All tests run strictly in-memory with transactional rollback and mocked Supabase Auth HTTP calls
so no real Supabase database rows, users, or schema objects are ever created or modified.
"""

import os
import uuid

# Configure valid PostgreSQL/Supabase test env vars BEFORE importing app modules
# (the actual test queries run against an isolated in-memory rollback session below).
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/cinetrack_test"
os.environ["SECRET_KEY"] = "test-secret-key-for-cinetrack-pytest-suite-min-32-bytes"
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "sb_publishable_mock_key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "sb_secret_mock_key"

from collections.abc import Generator  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Genre,
    Language,
    Movie,
    MovieGenre,
    MoviePlatform,
    StreamingPlatform,
    User,
)


@pytest.fixture(scope="session")
def test_engine():
    """Create an isolated in-memory test engine with foreign keys enforced and catalog seeded."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk_and_transactions(dbapi_connection, _connection_record) -> None:
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _emit_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN")

    Base.metadata.create_all(bind=engine)

    with Session(bind=engine) as session:
        lang_en = Language(language_name="English")
        lang_ko = Language(language_name="Korean")
        lang_ja = Language(language_name="Japanese")
        session.add_all([lang_en, lang_ko, lang_ja])

        g_scifi = Genre(genre_name="Sci-Fi")
        g_drama = Genre(genre_name="Drama")
        g_thriller = Genre(genre_name="Thriller")
        g_anim = Genre(genre_name="Animation")
        session.add_all([g_scifi, g_drama, g_thriller, g_anim])

        p_netflix = StreamingPlatform(streaming_platform_name="Netflix")
        p_prime = StreamingPlatform(streaming_platform_name="Amazon Prime Video")
        p_mubi = StreamingPlatform(streaming_platform_name="MUBI")
        session.add_all([p_netflix, p_prime, p_mubi])
        session.flush()

        m1 = Movie(
            title="Inception",
            release_yr=2010,
            duration=148,
            language_id=lang_en.language_id,
            description="Dream heist sci-fi thriller.",
            age_rating="PG-13",
        )
        m2 = Movie(
            title="Interstellar",
            release_yr=2014,
            duration=169,
            language_id=lang_en.language_id,
            description="Wormhole space exploration drama.",
            age_rating="PG-13",
        )
        m3 = Movie(
            title="Parasite",
            release_yr=2019,
            duration=132,
            language_id=lang_ko.language_id,
            description="Class satire thriller.",
            age_rating="R",
        )
        m4 = Movie(
            title="Spirited Away",
            release_yr=2001,
            duration=125,
            language_id=lang_ja.language_id,
            description="Animated spirit realm classic.",
            age_rating="PG",
        )
        session.add_all([m1, m2, m3, m4])
        session.flush()

        session.add_all(
            [
                MovieGenre(movie_id=m1.movie_id, genre_id=g_scifi.genre_id),
                MovieGenre(movie_id=m1.movie_id, genre_id=g_thriller.genre_id),
                MovieGenre(movie_id=m2.movie_id, genre_id=g_scifi.genre_id),
                MovieGenre(movie_id=m2.movie_id, genre_id=g_drama.genre_id),
                MovieGenre(movie_id=m3.movie_id, genre_id=g_drama.genre_id),
                MovieGenre(movie_id=m3.movie_id, genre_id=g_thriller.genre_id),
                MovieGenre(movie_id=m4.movie_id, genre_id=g_anim.genre_id),
            ]
        )
        session.add_all(
            [
                MoviePlatform(movie_id=m1.movie_id, platform_id=p_netflix.streaming_platform_id),
                MoviePlatform(movie_id=m1.movie_id, platform_id=p_prime.streaming_platform_id),
                MoviePlatform(movie_id=m2.movie_id, platform_id=p_prime.streaming_platform_id),
                MoviePlatform(movie_id=m3.movie_id, platform_id=p_mubi.streaming_platform_id),
                MoviePlatform(movie_id=m4.movie_id, platform_id=p_netflix.streaming_platform_id),
            ]
        )
        session.commit()

    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """Wrap each test in an outer transaction that rolls back after the test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def mock_supabase_auth(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate Supabase Auth endpoints and handle_new_user() trigger in-memory per test."""
    original_post = httpx.Client.post
    auth_users: dict[str, tuple[uuid.UUID, str]] = {}

    class _MockAuthResponse:
        def __init__(self, status_code: int, body: dict):
            self.status_code = status_code
            self._body = body
            self.content = b"{}"

        def json(self) -> dict:
            return self._body

    def _mock_post(self, url: str, *args, **kwargs):
        url_str = str(url)
        if not url_str.startswith("https://mock.supabase.co"):
            return original_post(self, url, *args, **kwargs)

        body = kwargs.get("json") or {}
        if url_str.endswith("/auth/v1/admin/users") or url_str.endswith("/auth/v1/signup"):
            email = str(body["email"])
            if email in auth_users:
                return _MockAuthResponse(422, {"msg": "User already registered"})
            metadata = body.get("user_metadata") or body.get("data") or {}
            username = str(metadata["username"])
            auth_uid = uuid.uuid4()
            auth_users[email] = (auth_uid, str(body["password"]))
            db_session.add(User(username=username, email=email, auth_user_id=auth_uid))
            db_session.flush()
            return _MockAuthResponse(200, {"id": str(auth_uid), "email": email})

        if "/auth/v1/token" in url_str:
            email = str(body["email"])
            record = auth_users.get(email)
            if record is not None and record[1] == str(body["password"]):
                return _MockAuthResponse(200, {"access_token": "mock-supa-jwt"})
            return _MockAuthResponse(400, {"error_description": "Invalid login credentials"})

        raise AssertionError(f"Unexpected Supabase Auth POST during tests: {url_str}")

    monkeypatch.setattr(httpx.Client, "post", _mock_post)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient wired to the per-test transactional DB session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_and_login(client: TestClient):
    """Factory fixture to register a user and return (user_dict, auth_headers)."""

    def _create(username: str, email: str, password: str = "securepass123"):
        reg_resp = client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert reg_resp.status_code == 201, reg_resp.text
        login_resp = client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]
        return reg_resp.json(), {"Authorization": f"Bearer {token}"}

    return _create


@pytest.fixture()
def user1_auth(register_and_login):
    """Authenticated primary test user."""
    return register_and_login("test_alice", "alice@example.com")


@pytest.fixture()
def user2_auth(register_and_login):
    """Authenticated secondary test user for ownership/authorization tests."""
    return register_and_login("test_bob", "bob@example.com")
