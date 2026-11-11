"""Review update and deletion routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.crud.review import delete_review, update_review
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import ReviewRead, ReviewUpdateRequest

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.put(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update your own review",
)
def put_review(
    review_id: int,
    payload: ReviewUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewRead:
    """Update rating, text, or streaming platform on the authenticated user's review."""
    return update_review(
        db,
        review_id=review_id,
        user_id=current_user.user_id,
        rating=payload.rating,
        review_text=payload.review_text,
        platform_id=payload.platform_id,
    )


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete your own review",
)
def remove_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a review written by the authenticated user."""
    delete_review(db, review_id=review_id, user_id=current_user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
