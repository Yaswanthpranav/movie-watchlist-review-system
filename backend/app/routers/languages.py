"""Language lookup routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.language import list_languages
from app.database import get_db
from app.schemas import LanguageRead

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("", response_model=list[LanguageRead], summary="List all movie languages")
def get_languages(db: Session = Depends(get_db)) -> list[LanguageRead]:
    """Return all available spoken languages."""
    return [LanguageRead.model_validate(lang) for lang in list_languages(db)]
