"""Watchlist and watchlist item routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.crud.watchlist import (
    add_watchlist_item,
    create_watchlist,
    create_watchlist_with_items,
    delete_watchlist,
    get_watchlist_detail,
    list_user_watchlists,
    remove_watchlist_item,
    update_watchlist_item_status,
)
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    WatchlistCreateRequest,
    WatchlistDetailRead,
    WatchlistItemCreateRequest,
    WatchlistItemRead,
    WatchlistItemStatusUpdateRequest,
    WatchlistSummaryRead,
    WatchlistWithItemsCreateRequest,
)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


@router.post(
    "",
    response_model=WatchlistSummaryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new watchlist",
)
def post_watchlist(
    payload: WatchlistCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistSummaryRead:
    """Create a named watchlist owned by the authenticated user."""
    return create_watchlist(
        db,
        user_id=current_user.user_id,
        watchlist_name=payload.watchlist_name,
        notes=payload.notes,
    )


@router.post(
    "/with-items",
    response_model=WatchlistDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Atomically create a watchlist with initial movies (explicit transaction)",
)
def post_watchlist_with_items(
    payload: WatchlistWithItemsCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistDetailRead:
    """Create a watchlist and all initial items in one explicit atomic transaction."""
    return create_watchlist_with_items(
        db,
        user_id=current_user.user_id,
        watchlist_name=payload.watchlist_name,
        notes=payload.notes,
        items=payload.items,
    )


@router.get(
    "",
    response_model=list[WatchlistSummaryRead],
    summary="List current user's watchlists",
)
def get_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchlistSummaryRead]:
    """Return all watchlists owned by the authenticated user."""
    return list_user_watchlists(db, user_id=current_user.user_id)


@router.get(
    "/{watchlist_id}",
    response_model=WatchlistDetailRead,
    summary="Get a watchlist with its movies",
)
def get_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistDetailRead:
    """Return a watchlist and its items if owned by the authenticated user."""
    return get_watchlist_detail(
        db,
        watchlist_id=watchlist_id,
        user_id=current_user.user_id,
    )


@router.delete(
    "/{watchlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a watchlist",
)
def remove_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a watchlist owned by the authenticated user."""
    delete_watchlist(db, watchlist_id=watchlist_id, user_id=current_user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a movie to a watchlist",
)
def post_watchlist_item(
    watchlist_id: int,
    payload: WatchlistItemCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemRead:
    """Add a movie to the user's watchlist."""
    return add_watchlist_item(
        db,
        watchlist_id=watchlist_id,
        user_id=current_user.user_id,
        movie_id=payload.movie_id,
        item_status=payload.status,
    )


@router.patch(
    "/{watchlist_id}/items/{movie_id}",
    response_model=WatchlistItemRead,
    summary="Update a movie's viewing status in a watchlist",
)
def patch_watchlist_item(
    watchlist_id: int,
    movie_id: int,
    payload: WatchlistItemStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemRead:
    """Update a watchlist movie's status ('PLANNED', 'WATCHING', 'COMPLETED')."""
    return update_watchlist_item_status(
        db,
        watchlist_id=watchlist_id,
        user_id=current_user.user_id,
        movie_id=movie_id,
        new_status=payload.status,
    )


@router.delete(
    "/{watchlist_id}/items/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a movie from a watchlist",
)
def delete_watchlist_item(
    watchlist_id: int,
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Remove a movie from the user's watchlist."""
    remove_watchlist_item(
        db,
        watchlist_id=watchlist_id,
        user_id=current_user.user_id,
        movie_id=movie_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
