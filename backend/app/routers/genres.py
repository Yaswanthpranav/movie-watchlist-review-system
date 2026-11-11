"""Genre lookup routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.genre import list_genres
from app.database import get_db
from app.schemas import GenreRead

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=list[GenreRead], summary="List all movie genres")
def get_genres(db: Session = Depends(get_db)) -> list[GenreRead]:
    """Return all available movie genres."""
    return [GenreRead.model_validate(genre) for genre in list_genres(db)]
