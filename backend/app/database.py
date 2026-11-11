"""PostgreSQL (Supabase) database engine, session factory, and FastAPI dependency."""

from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def _normalize_database_url(raw_url: str) -> str:
    """Validate PostgreSQL URI and select psycopg2 when psycopg v3 is absent."""
    cleaned = raw_url.strip()
    if cleaned.startswith("postgres://"):
        cleaned = cleaned.replace("postgres://", "postgresql://", 1)

    if not (
        cleaned.startswith("postgresql://")
        or cleaned.startswith("postgresql+psycopg2://")
    ):
        raise ValueError(
            "Only PostgreSQL (Supabase) DATABASE_URL values are supported."
        )

    if cleaned.startswith("postgresql://"):
        try:
            import psycopg  # noqa: F401
        except ImportError:
            cleaned = cleaned.replace("postgresql://", "postgresql+psycopg2://", 1)
    return cleaned


def build_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy Engine configured strictly for PostgreSQL on Supabase."""
    normalized = _normalize_database_url(database_url)
    return create_engine(normalized, pool_pre_ping=True)


settings = get_settings()
engine = build_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy Session and close it after the request finishes."""
    if "[YOUR-PASSWORD]" in settings.DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database password not configured: replace [YOUR-PASSWORD] in backend/.env "
                "with your Supabase Postgres password (using the Session pooler URI on port 5432)."
            ),
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
