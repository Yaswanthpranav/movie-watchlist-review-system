"""CRUD operations for the Genre lookup entity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Genre


def list_genres(db: Session) -> list[Genre]:
    """Return all genres ordered alphabetically."""
    stmt = select(Genre).order_by(Genre.genre_name.asc())
    return list(db.scalars(stmt).all())
