"""Streaming platform lookup routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.platform import list_platforms
from app.database import get_db
from app.schemas import PlatformRead

router = APIRouter(prefix="/platforms", tags=["Platforms"])


@router.get(
    "",
    response_model=list[PlatformRead],
    summary="List all streaming platforms",
)
def get_platforms(db: Session = Depends(get_db)) -> list[PlatformRead]:
    """Return all available streaming platforms."""
    return [PlatformRead.model_validate(p) for p in list_platforms(db)]
