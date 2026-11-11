"""CRUD operations and explicit transaction workflow for Watchlist entities."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import translate_integrity_error
from app.models import Language, Movie, Watchlist, WatchlistItem
from app.schemas import (
    WatchlistDetailRead,
    WatchlistItemCreateRequest,
    WatchlistItemMovieInfo,
    WatchlistItemRead,
    WatchlistStatus,
    WatchlistSummaryRead,
)


def _get_watchlist_for_owner(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
) -> Watchlist:
    """Fetch a watchlist or raise 404 if missing, 403 if owned by another user."""
    watchlist = db.get(Watchlist, watchlist_id)
    if watchlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found.",
        )
    if watchlist.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this watchlist.",
        )
    return watchlist


def _fetch_watchlist_item_read(
    db: Session,
    *,
    watchlist_item_id: int,
) -> WatchlistItemRead:
    """Fetch a single WatchlistItem joined with Movie & Language metadata."""
    row = db.execute(
        select(
            WatchlistItem.watchlist_item_id,
            WatchlistItem.watchlist_id,
            WatchlistItem.movie_id,
            WatchlistItem.added_date,
            WatchlistItem.status,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Movie.age_rating,
            Language.language_name,
        )
        .join(Movie, Movie.movie_id == WatchlistItem.movie_id)
        .join(Language, Language.language_id == Movie.language_id)
        .where(WatchlistItem.watchlist_item_id == watchlist_item_id)
    ).one()

    return WatchlistItemRead(
        watchlist_item_id=row.watchlist_item_id,
        watchlist_id=row.watchlist_id,
        movie_id=row.movie_id,
        added_date=row.added_date,
        status=row.status,
        movie=WatchlistItemMovieInfo(
            movie_id=row.movie_id,
            title=row.title,
            release_yr=row.release_yr,
            duration=row.duration,
            age_rating=row.age_rating,
            language_name=row.language_name,
        ),
    )


def create_watchlist(
    db: Session,
    *,
    user_id: int,
    watchlist_name: str,
    notes: str | None = None,
) -> WatchlistSummaryRead:
    """Create a new watchlist owned by the authenticated user."""
    watchlist = Watchlist(
        user_id=user_id,
        watchlist_name=watchlist_name,
        notes=notes,
    )
    db.add(watchlist)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise translate_integrity_error(exc) from exc
    db.refresh(watchlist)
    return WatchlistSummaryRead(
        watchlist_id=watchlist.watchlist_id,
        user_id=watchlist.user_id,
        watchlist_name=watchlist.watchlist_name,
        notes=watchlist.notes,
        create_date=watchlist.create_date,
        item_count=0,
    )


def create_watchlist_with_items(
    db: Session,
    *,
    user_id: int,
    watchlist_name: str,
    notes: str | None,
    items: list[WatchlistItemCreateRequest],
) -> WatchlistDetailRead:
    """Atomically create a watchlist and initial movie items inside an explicit transaction.

    If any item violates a foreign-key or unique constraint, the entire transaction
    rolls back so no partial watchlist or partial items remain in the database.
    """
    already_in_tx = db.in_transaction()
    tx = db.begin_nested() if already_in_tx else db.begin()
    try:
        with tx:
            watchlist = Watchlist(
                user_id=user_id,
                watchlist_name=watchlist_name,
                notes=notes,
            )
            db.add(watchlist)
            db.flush()

            for entry in items:
                db.add(
                    WatchlistItem(
                        watchlist_id=watchlist.watchlist_id,
                        movie_id=entry.movie_id,
                        status=entry.status,
                    )
                )
            db.flush()
    except IntegrityError as exc:
        raise translate_integrity_error(exc) from exc

    if already_in_tx:
        db.commit()
    return get_watchlist_detail(
        db,
        watchlist_id=watchlist.watchlist_id,
        user_id=user_id,
    )


def list_user_watchlists(db: Session, *, user_id: int) -> list[WatchlistSummaryRead]:
    """Return all watchlists belonging to the current user with item counts."""
    rows = db.execute(
        select(
            Watchlist.watchlist_id,
            Watchlist.user_id,
            Watchlist.watchlist_name,
            Watchlist.notes,
            Watchlist.create_date,
            func.count(WatchlistItem.watchlist_item_id).label("item_count"),
        )
        .outerjoin(WatchlistItem, WatchlistItem.watchlist_id == Watchlist.watchlist_id)
        .where(Watchlist.user_id == user_id)
        .group_by(
            Watchlist.watchlist_id,
            Watchlist.user_id,
            Watchlist.watchlist_name,
            Watchlist.notes,
            Watchlist.create_date,
        )
        .order_by(Watchlist.create_date.desc(), Watchlist.watchlist_id.desc())
    ).all()

    return [
        WatchlistSummaryRead(
            watchlist_id=row.watchlist_id,
            user_id=row.user_id,
            watchlist_name=row.watchlist_name,
            notes=row.notes,
            create_date=row.create_date,
            item_count=int(row.item_count or 0),
        )
        for row in rows
    ]


def get_watchlist_detail(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
) -> WatchlistDetailRead:
    """Return a watchlist and all its items with movie info for the owner."""
    watchlist = _get_watchlist_for_owner(
        db, watchlist_id=watchlist_id, user_id=user_id
    )

    rows = db.execute(
        select(
            WatchlistItem.watchlist_item_id,
            WatchlistItem.watchlist_id,
            WatchlistItem.movie_id,
            WatchlistItem.added_date,
            WatchlistItem.status,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Movie.age_rating,
            Language.language_name,
        )
        .join(Movie, Movie.movie_id == WatchlistItem.movie_id)
        .join(Language, Language.language_id == Movie.language_id)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.added_date.desc(), WatchlistItem.watchlist_item_id.desc())
    ).all()

    items = [
        WatchlistItemRead(
            watchlist_item_id=row.watchlist_item_id,
            watchlist_id=row.watchlist_id,
            movie_id=row.movie_id,
            added_date=row.added_date,
            status=row.status,
            movie=WatchlistItemMovieInfo(
                movie_id=row.movie_id,
                title=row.title,
                release_yr=row.release_yr,
                duration=row.duration,
                age_rating=row.age_rating,
                language_name=row.language_name,
            ),
        )
        for row in rows
    ]

    return WatchlistDetailRead(
        watchlist_id=watchlist.watchlist_id,
        user_id=watchlist.user_id,
        watchlist_name=watchlist.watchlist_name,
        notes=watchlist.notes,
        create_date=watchlist.create_date,
        items=items,
    )


def delete_watchlist(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
) -> None:
    """Delete a watchlist owned by the current user."""
    watchlist = _get_watchlist_for_owner(
        db, watchlist_id=watchlist_id, user_id=user_id
    )
    db.delete(watchlist)
    db.commit()


def add_watchlist_item(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
    movie_id: int,
    item_status: WatchlistStatus = "PLANNED",
) -> WatchlistItemRead:
    """Add a movie to a user's watchlist; DB enforces FK and UNIQUE(watchlist_id, movie_id)."""
    _get_watchlist_for_owner(db, watchlist_id=watchlist_id, user_id=user_id)

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        movie_id=movie_id,
        status=item_status,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise translate_integrity_error(exc) from exc

    db.refresh(item)
    return _fetch_watchlist_item_read(db, watchlist_item_id=item.watchlist_item_id)


def update_watchlist_item_status(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
    movie_id: int,
    new_status: WatchlistStatus,
) -> WatchlistItemRead:
    """Update the status of a movie inside a user's watchlist."""
    _get_watchlist_for_owner(db, watchlist_id=watchlist_id, user_id=user_id)

    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.movie_id == movie_id,
        )
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in this watchlist.",
        )

    item.status = new_status
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise translate_integrity_error(exc) from exc

    db.refresh(item)
    return _fetch_watchlist_item_read(db, watchlist_item_id=item.watchlist_item_id)


def remove_watchlist_item(
    db: Session,
    *,
    watchlist_id: int,
    user_id: int,
    movie_id: int,
) -> None:
    """Remove a movie from a user's watchlist."""
    _get_watchlist_for_owner(db, watchlist_id=watchlist_id, user_id=user_id)

    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.movie_id == movie_id,
        )
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in this watchlist.",
        )

    db.delete(item)
    db.commit()
