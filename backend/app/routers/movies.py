"""Movie catalog, ranking, and movie review routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.movie import (
    MovieSort,
    get_movie_detail,
    get_top_rated_movies,
    list_movies,
)
from app.crud.review import create_review, list_movie_reviews
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    MovieDetailResponse,
    MovieListResponse,
    ReviewCreateRequest,
    ReviewRead,
    TopRatedMovieItem,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=MovieListResponse, summary="Browse and filter movies")
def get_movies(
    search: str | None = Query(default=None, description="Search title or description"),
    genre_id: int | None = Query(default=None, ge=1),
    language_id: int | None = Query(default=None, ge=1),
    platform_id: int | None = Query(default=None, ge=1),
    year: int | None = Query(default=None, ge=1888, le=2100),
    min_rating: float | None = Query(default=None, ge=1.0, le=5.0),
    sort: MovieSort = Query(default=MovieSort.TITLE_ASC),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> MovieListResponse:
    """Return paginated movies with AVG rating and review count computed via SQL aggregation."""
    return list_movies(
        db,
        search=search,
        genre_id=genre_id,
        language_id=language_id,
        platform_id=platform_id,
        year=year,
        min_rating=min_rating,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/top-rated",
    response_model=list[TopRatedMovieItem],
    summary="Top-rated movies ranked via SQL RANK() OVER",
)
def get_top_rated(
    limit: int = Query(default=10, ge=1, le=50),
    min_reviews: int = Query(default=1, ge=0, le=1000),
    db: Session = Depends(get_db),
) -> list[TopRatedMovieItem]:
    """Return top-rated movies computed with a CTE and window function RANK() OVER."""
    return get_top_rated_movies(db, limit=limit, min_reviews=min_reviews)


@router.get(
    "/{movie_id}",
    response_model=MovieDetailResponse,
    summary="Get movie details, tags, platforms, and rating summary",
)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailResponse:
    """Return full details for a single movie by ID."""
    movie = get_movie_detail(db, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found.",
        )
    return movie


@router.get(
    "/{movie_id}/reviews",
    response_model=list[ReviewRead],
    summary="List reviews for a movie",
)
def get_movie_reviews(movie_id: int, db: Session = Depends(get_db)) -> list[ReviewRead]:
    """Return all user reviews for the specified movie."""
    return list_movie_reviews(db, movie_id=movie_id)


@router.post(
    "/{movie_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post a rating and review for a movie",
)
def post_movie_review(
    movie_id: int,
    payload: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewRead:
    """Create a review for a movie using the authenticated user from the JWT token."""
    return create_review(
        db,
        user_id=current_user.user_id,
        movie_id=movie_id,
        rating=payload.rating,
        review_text=payload.review_text,
        platform_id=payload.platform_id,
    )
