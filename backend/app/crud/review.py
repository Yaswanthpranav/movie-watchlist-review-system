"""CRUD operations for the Review entity."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.movie import movie_exists
from app.exceptions import translate_integrity_error
from app.models import Review, StreamingPlatform, User
from app.schemas import ReviewRead


def _fetch_review_read(db: Session, *, review_id: int) -> ReviewRead:
    """Fetch a review joined with username and optional platform name."""
    row = db.execute(
        select(
            Review.review_id,
            Review.user_id,
            User.username,
            Review.movie_id,
            Review.platform_id,
            StreamingPlatform.streaming_platform_name.label("platform_name"),
            Review.rating,
            Review.review_text,
            Review.reviewed_on,
        )
        .join(User, User.user_id == Review.user_id)
        .outerjoin(
            StreamingPlatform,
            StreamingPlatform.streaming_platform_id == Review.platform_id,
        )
        .where(Review.review_id == review_id)
    ).one()

    return ReviewRead(
        review_id=row.review_id,
        user_id=row.user_id,
        username=row.username,
        movie_id=row.movie_id,
        platform_id=row.platform_id,
        platform_name=row.platform_name,
        rating=float(row.rating),
        review_text=row.review_text,
        reviewed_on=row.reviewed_on,
    )


def _get_review_for_owner(
    db: Session,
    *,
    review_id: int,
    user_id: int,
) -> Review:
    """Fetch a review or raise 404 if missing, 403 if written by another user."""
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )
    if review.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this review.",
        )
    return review


def list_movie_reviews(db: Session, *, movie_id: int) -> list[ReviewRead]:
    """Return all reviews for a movie ordered newest first."""
    if not movie_exists(db, movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    rows = db.execute(
        select(
            Review.review_id,
            Review.user_id,
            User.username,
            Review.movie_id,
            Review.platform_id,
            StreamingPlatform.streaming_platform_name.label("platform_name"),
            Review.rating,
            Review.review_text,
            Review.reviewed_on,
        )
        .join(User, User.user_id == Review.user_id)
        .outerjoin(
            StreamingPlatform,
            StreamingPlatform.streaming_platform_id == Review.platform_id,
        )
        .where(Review.movie_id == movie_id)
        .order_by(Review.reviewed_on.desc(), Review.review_id.desc())
    ).all()

    return [
        ReviewRead(
            review_id=row.review_id,
            user_id=row.user_id,
            username=row.username,
            movie_id=row.movie_id,
            platform_id=row.platform_id,
            platform_name=row.platform_name,
            rating=float(row.rating),
            review_text=row.review_text,
            reviewed_on=row.reviewed_on,
        )
        for row in rows
    ]


def create_review(
    db: Session,
    *,
    user_id: int,
    movie_id: int,
    rating: int,
    review_text: str | None = None,
    platform_id: int | None = None,
) -> ReviewRead:
    """Create a review for a movie; enforces unique (user_id, movie_id) and rating check."""
    if not movie_exists(db, movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )

    review = Review(
        user_id=user_id,
        movie_id=movie_id,
        platform_id=platform_id,
        rating=rating,
        review_text=review_text,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise translate_integrity_error(exc) from exc

    db.refresh(review)
    return _fetch_review_read(db, review_id=review.review_id)


def update_review(
    db: Session,
    *,
    review_id: int,
    user_id: int,
    rating: int,
    review_text: str | None = None,
    platform_id: int | None = None,
) -> ReviewRead:
    """Update an existing review belonging to the authenticated user."""
    review = _get_review_for_owner(db, review_id=review_id, user_id=user_id)
    review.rating = rating
    review.review_text = review_text
    review.platform_id = platform_id
    review.reviewed_on = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise translate_integrity_error(exc) from exc

    db.refresh(review)
    return _fetch_review_read(db, review_id=review.review_id)


def delete_review(
    db: Session,
    *,
    review_id: int,
    user_id: int,
) -> None:
    """Delete an existing review belonging to the authenticated user."""
    review = _get_review_for_owner(db, review_id=review_id, user_id=user_id)
    db.delete(review)
    db.commit()
