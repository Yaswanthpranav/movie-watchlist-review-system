"""CRUD operations for the StreamingPlatform lookup entity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StreamingPlatform


def list_platforms(db: Session) -> list[StreamingPlatform]:
    """Return all streaming platforms ordered alphabetically."""
    stmt = select(StreamingPlatform).order_by(
        StreamingPlatform.streaming_platform_name.asc()
    )
    return list(db.scalars(stmt).all())
