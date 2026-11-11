"""CRUD operations and SQL aggregate/window queries for the Movie entity."""

from collections import defaultdict
from enum import Enum

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Genre,
    Language,
    Movie,
    MovieGenre,
    MoviePlatform,
    Review,
    StreamingPlatform,
)
from app.schemas import (
    GenreRead,
    LanguageRead,
    MovieDetailResponse,
    MovieListResponse,
    MovieSummary,
    PlatformRead,
    TopRatedMovieItem,
)


class MovieSort(str, Enum):
    """Allowed sorting options for movie catalog listing."""

    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    YEAR_DESC = "year_desc"
    YEAR_ASC = "year_asc"
    RATING_DESC = "rating_desc"
    RATING_ASC = "rating_asc"
    REVIEWS_DESC = "reviews_desc"


def movie_exists(db: Session, movie_id: int) -> bool:
    """Return True if a movie with the given ID exists."""
    stmt = select(exists().where(Movie.movie_id == movie_id))
    return bool(db.scalar(stmt))


def _load_movie_tags(
    db: Session, movie_ids: list[int]
) -> tuple[dict[int, list[GenreRead]], dict[int, list[PlatformRead]]]:
    """Batch-load genres and streaming platforms for a set of movie IDs (no N+1 queries)."""
    genres_map: dict[int, list[GenreRead]] = defaultdict(list)
    platforms_map: dict[int, list[PlatformRead]] = defaultdict(list)
    if not movie_ids:
        return genres_map, platforms_map

    genre_rows = db.execute(
        select(MovieGenre.movie_id, Genre.genre_id, Genre.genre_name)
        .join(Genre, Genre.genre_id == MovieGenre.genre_id)
        .where(MovieGenre.movie_id.in_(movie_ids))
        .order_by(Genre.genre_name.asc())
    ).all()
    for mid, gid, gname in genre_rows:
        genres_map[mid].append(GenreRead(genre_id=gid, genre_name=gname))

    platform_rows = db.execute(
        select(
            MoviePlatform.movie_id,
            StreamingPlatform.streaming_platform_id,
            StreamingPlatform.streaming_platform_name,
        )
        .join(
            StreamingPlatform,
            StreamingPlatform.streaming_platform_id == MoviePlatform.platform_id,
        )
        .where(MoviePlatform.movie_id.in_(movie_ids))
        .order_by(StreamingPlatform.streaming_platform_name.asc())
    ).all()
    for mid, pid, pname in platform_rows:
        platforms_map[mid].append(
            PlatformRead(streaming_platform_id=pid, streaming_platform_name=pname)
        )

    return genres_map, platforms_map


def list_movies(
    db: Session,
    *,
    search: str | None = None,
    genre_id: int | None = None,
    language_id: int | None = None,
    platform_id: int | None = None,
    year: int | None = None,
    min_rating: float | None = None,
    sort: MovieSort = MovieSort.TITLE_ASC,
    page: int = 1,
    page_size: int = 20,
) -> MovieListResponse:
    """List movies with filters, SQL AVG/COUNT aggregation, sorting, and pagination."""
    avg_expr = func.avg(Review.rating)
    count_expr = func.count(Review.review_id)

    base_stmt = (
        select(
            Movie.movie_id,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Movie.language_id,
            Language.language_name,
            Movie.description,
            Movie.age_rating,
            avg_expr.label("average_rating"),
            count_expr.label("review_count"),
        )
        .join(Language, Language.language_id == Movie.language_id)
        .outerjoin(Review, Review.movie_id == Movie.movie_id)
    )

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base_stmt = base_stmt.where(
            or_(Movie.title.ilike(pattern), Movie.description.ilike(pattern))
        )
    if language_id is not None:
        base_stmt = base_stmt.where(Movie.language_id == language_id)
    if year is not None:
        base_stmt = base_stmt.where(Movie.release_yr == year)
    if genre_id is not None:
        base_stmt = base_stmt.where(
            exists().where(
                MovieGenre.movie_id == Movie.movie_id,
                MovieGenre.genre_id == genre_id,
            )
        )
    if platform_id is not None:
        base_stmt = base_stmt.where(
            exists().where(
                MoviePlatform.movie_id == Movie.movie_id,
                MoviePlatform.platform_id == platform_id,
            )
        )

    grouped_stmt = base_stmt.group_by(
        Movie.movie_id,
        Movie.title,
        Movie.release_yr,
        Movie.duration,
        Movie.language_id,
        Language.language_name,
        Movie.description,
        Movie.age_rating,
    )

    if min_rating is not None:
        grouped_stmt = grouped_stmt.having(avg_expr >= min_rating)

    total = int(
        db.scalar(select(func.count()).select_from(grouped_stmt.subquery())) or 0
    )

    sort_map = {
        MovieSort.TITLE_ASC: (Movie.title.asc(), Movie.movie_id.asc()),
        MovieSort.TITLE_DESC: (Movie.title.desc(), Movie.movie_id.asc()),
        MovieSort.YEAR_DESC: (Movie.release_yr.desc(), Movie.movie_id.asc()),
        MovieSort.YEAR_ASC: (Movie.release_yr.asc(), Movie.movie_id.asc()),
        MovieSort.RATING_DESC: (avg_expr.desc().nulls_last(), count_expr.desc(), Movie.movie_id.asc()),
        MovieSort.RATING_ASC: (avg_expr.asc().nulls_last(), Movie.movie_id.asc()),
        MovieSort.REVIEWS_DESC: (count_expr.desc(), avg_expr.desc().nulls_last(), Movie.movie_id.asc()),
    }

    offset = (page - 1) * page_size
    rows = db.execute(
        grouped_stmt.order_by(*sort_map[sort]).limit(page_size).offset(offset)
    ).all()

    movie_ids = [row.movie_id for row in rows]
    genres_map, platforms_map = _load_movie_tags(db, movie_ids)

    items = [
        MovieSummary(
            movie_id=row.movie_id,
            title=row.title,
            release_yr=row.release_yr,
            duration=row.duration,
            language_id=row.language_id,
            language_name=row.language_name,
            description=row.description,
            age_rating=row.age_rating,
            genres=genres_map.get(row.movie_id, []),
            platforms=platforms_map.get(row.movie_id, []),
            average_rating=(
                round(float(row.average_rating), 2)
                if row.average_rating is not None
                else None
            ),
            review_count=int(row.review_count or 0),
        )
        for row in rows
    ]

    return MovieListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def get_movie_detail(db: Session, movie_id: int) -> MovieDetailResponse | None:
    """Return full details for a single movie with aggregated rating and tags."""
    row = db.execute(
        select(
            Movie.movie_id,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Movie.description,
            Movie.age_rating,
            Language.language_id,
            Language.language_name,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.review_id).label("review_count"),
        )
        .join(Language, Language.language_id == Movie.language_id)
        .outerjoin(Review, Review.movie_id == Movie.movie_id)
        .where(Movie.movie_id == movie_id)
        .group_by(
            Movie.movie_id,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Movie.description,
            Movie.age_rating,
            Language.language_id,
            Language.language_name,
        )
    ).first()

    if row is None:
        return None

    genres_map, platforms_map = _load_movie_tags(db, [movie_id])

    return MovieDetailResponse(
        movie_id=row.movie_id,
        title=row.title,
        release_yr=row.release_yr,
        duration=row.duration,
        language=LanguageRead(
            language_id=row.language_id,
            language_name=row.language_name,
        ),
        description=row.description,
        age_rating=row.age_rating,
        genres=genres_map.get(movie_id, []),
        platforms=platforms_map.get(movie_id, []),
        average_rating=(
            round(float(row.average_rating), 2)
            if row.average_rating is not None
            else None
        ),
        review_count=int(row.review_count or 0),
    )


def get_top_rated_movies(
    db: Session,
    *,
    limit: int = 10,
    min_reviews: int = 1,
) -> list[TopRatedMovieItem]:
    """Rank top-rated movies using a CTE and SQL RANK() OVER window function."""
    stats_cte = (
        select(
            Movie.movie_id.label("movie_id"),
            Movie.title.label("title"),
            Movie.release_yr.label("release_yr"),
            Movie.duration.label("duration"),
            Language.language_name.label("language_name"),
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.review_id).label("review_count"),
        )
        .join(Language, Language.language_id == Movie.language_id)
        .outerjoin(Review, Review.movie_id == Movie.movie_id)
        .group_by(
            Movie.movie_id,
            Movie.title,
            Movie.release_yr,
            Movie.duration,
            Language.language_name,
        )
        .having(func.count(Review.review_id) >= min_reviews)
        .cte("movie_stats")
    )

    ranked_cte = (
        select(
            func.rank()
            .over(
                order_by=(
                    func.coalesce(stats_cte.c.avg_rating, 0).desc(),
                    stats_cte.c.review_count.desc(),
                )
            )
            .label("movie_rank"),
            stats_cte.c.movie_id,
            stats_cte.c.title,
            stats_cte.c.release_yr,
            stats_cte.c.duration,
            stats_cte.c.language_name,
            stats_cte.c.avg_rating,
            stats_cte.c.review_count,
        )
    ).cte("ranked_movies")

    ranked_stmt = (
        select(ranked_cte)
        .order_by(ranked_cte.c.movie_rank.asc(), ranked_cte.c.movie_id.asc())
        .limit(limit)
    )

    rows = db.execute(ranked_stmt).all()
    return [
        TopRatedMovieItem(
            rank=int(row.movie_rank),
            movie_id=row.movie_id,
            title=row.title,
            release_yr=row.release_yr,
            duration=row.duration,
            language_name=row.language_name,
            average_rating=(
                round(float(row.avg_rating), 2)
                if row.avg_rating is not None
                else None
            ),
            review_count=int(row.review_count or 0),
        )
        for row in rows
    ]
