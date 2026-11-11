"""CRUD operations for the Language lookup entity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Language


def list_languages(db: Session) -> list[Language]:
    """Return all languages ordered alphabetically."""
    stmt = select(Language).order_by(Language.language_name.asc())
    return list(db.scalars(stmt).all())
