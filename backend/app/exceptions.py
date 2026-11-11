"""Database integrity error translation to clean HTTP 409 Conflict responses."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


def translate_integrity_error(exc: IntegrityError) -> HTTPException:
    """Translate PostgreSQL and SQLite IntegrityError exceptions into HTTP 409 errors."""
    orig = exc.orig
    pgcode = getattr(orig, "pgcode", None)
    raw_msg = str(orig) if orig is not None else str(exc)
    lower_msg = raw_msg.lower()

    if pgcode == "23505" or "unique constraint failed" in lower_msg or "duplicate key" in lower_msg:
        if "username" in lower_msg:
            detail = "Username is already taken."
        elif "email" in lower_msg:
            detail = "Email is already registered."
        elif "auth_user_id" in lower_msg:
            detail = "Auth user is already linked to an account."
        elif "watchlist_user_name_unique" in lower_msg or (
            "watchlist" in lower_msg and "watchlist_name" in lower_msg
        ):
            detail = "You already have a watchlist with this name."
        elif "watchlist_movie_unique" in lower_msg or "watchlist_items" in lower_msg or (
            "watchlist_id" in lower_msg and "movie_id" in lower_msg
        ):
            detail = "Movie is already in this watchlist."
        elif "reviews_user_movie_unique" in lower_msg or "reviews" in lower_msg or (
            "user_id" in lower_msg and "movie_id" in lower_msg
        ):
            detail = "You have already reviewed this movie."
        elif "language_name" in lower_msg:
            detail = "Language already exists."
        elif "genre_name" in lower_msg:
            detail = "Genre already exists."
        elif "streaming_platform_name" in lower_msg:
            detail = "Streaming platform already exists."
        else:
            detail = "Resource conflicts with an existing unique record."
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    if pgcode == "23503" or "foreign key constraint failed" in lower_msg or "violates foreign key constraint" in lower_msg:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Referenced record does not exist (foreign key constraint violation).",
        )

    if pgcode == "23514" or "check constraint failed" in lower_msg or "violates check constraint" in lower_msg:
        if "rating" in lower_msg:
            detail = "Rating must be between 1 and 5."
        elif "status" in lower_msg:
            detail = "Status must be one of: 'PLANNED', 'WATCHING', 'COMPLETED'."
        elif "duration" in lower_msg:
            detail = "Movie duration must be a positive integer."
        else:
            detail = "Value violates a database check constraint."
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    if pgcode == "23502" or "not null constraint failed" in lower_msg:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A required database column cannot be null.",
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Database integrity constraint conflict.",
    )
