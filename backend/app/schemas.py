"""Pydantic v2 request and response schemas aligned with live Supabase schema."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

WatchlistStatus = Literal["PLANNED", "WATCHING", "COMPLETED"]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str


# ---------------------------------------------------------------------------
# Auth & User Schemas (never expose any secret or password hash)
# ---------------------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    """Request body for user registration."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Username must be at least 3 non-whitespace characters.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 UTF-8 bytes.")
        return value


class UserLoginRequest(BaseModel):
    """Request body for user login (supports username or email)."""

    username: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str = Field(..., min_length=1, max_length=72)

    @model_validator(mode="after")
    def require_identifier(self) -> "UserLoginRequest":
        if not self.username and not self.email:
            raise ValueError("Either username or email must be provided.")
        return self


class UserRead(BaseModel):
    """Public user representation matching live public."user" table."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: EmailStr
    create_date: datetime
    auth_user_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    """JWT access token response returned on login."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ---------------------------------------------------------------------------
# Lookup Schemas
# ---------------------------------------------------------------------------
class LanguageRead(BaseModel):
    """Language lookup item."""

    model_config = ConfigDict(from_attributes=True)

    language_id: int
    language_name: str


class GenreRead(BaseModel):
    """Genre lookup item."""

    model_config = ConfigDict(from_attributes=True)

    genre_id: int
    genre_name: str


class PlatformRead(BaseModel):
    """Streaming platform lookup item."""

    model_config = ConfigDict(from_attributes=True)

    streaming_platform_id: int
    streaming_platform_name: str


# ---------------------------------------------------------------------------
# Movie Schemas
# ---------------------------------------------------------------------------
class MovieSummary(BaseModel):
    """Catalog movie entry with aggregated rating metrics and tags."""

    movie_id: int
    title: str
    release_yr: int | None = None
    duration: int
    language_id: int
    language_name: str
    description: str | None = None
    age_rating: str | None = None
    genres: list[GenreRead] = Field(default_factory=list)
    platforms: list[PlatformRead] = Field(default_factory=list)
    average_rating: float | None = None
    review_count: int = 0


class MovieListResponse(BaseModel):
    """Paginated movie catalog response."""

    items: list[MovieSummary]
    total: int
    page: int
    page_size: int


class MovieDetailResponse(BaseModel):
    """Detailed single movie response."""

    movie_id: int
    title: str
    release_yr: int | None = None
    duration: int
    language: LanguageRead
    description: str | None = None
    age_rating: str | None = None
    genres: list[GenreRead] = Field(default_factory=list)
    platforms: list[PlatformRead] = Field(default_factory=list)
    average_rating: float | None = None
    review_count: int = 0


class TopRatedMovieItem(BaseModel):
    """Top-rated movie ranked via SQL window function RANK() OVER."""

    rank: int
    movie_id: int
    title: str
    release_yr: int | None = None
    duration: int
    language_name: str
    average_rating: float | None = None
    review_count: int


# ---------------------------------------------------------------------------
# Watchlist Schemas
# ---------------------------------------------------------------------------
class WatchlistCreateRequest(BaseModel):
    """Request body to create a watchlist (accepts watchlist_name or name)."""

    watchlist_name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        validation_alias=AliasChoices("watchlist_name", "name"),
    )
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("watchlist_name")
    @classmethod
    def validate_watchlist_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Watchlist name cannot be blank.")
        return cleaned


class WatchlistItemCreateRequest(BaseModel):
    """Request body to add a movie to a watchlist."""

    movie_id: int = Field(..., ge=1)
    status: WatchlistStatus = "PLANNED"


class WatchlistWithItemsCreateRequest(WatchlistCreateRequest):
    """Request body to atomically create a watchlist and initial movie items."""

    items: list[WatchlistItemCreateRequest] = Field(..., min_length=1, max_length=50)


class WatchlistItemStatusUpdateRequest(BaseModel):
    """Request body to update a watchlist item's viewing status."""

    status: WatchlistStatus


class WatchlistItemMovieInfo(BaseModel):
    """Movie summary embedded inside a watchlist item."""

    movie_id: int
    title: str
    release_yr: int | None = None
    duration: int
    age_rating: str | None = None
    language_name: str


class WatchlistItemRead(BaseModel):
    """Watchlist item response."""

    watchlist_item_id: int
    watchlist_id: int
    movie_id: int
    added_date: datetime
    status: WatchlistStatus
    movie: WatchlistItemMovieInfo


class WatchlistSummaryRead(BaseModel):
    """Summary of a user's watchlist."""

    watchlist_id: int
    user_id: int
    watchlist_name: str
    notes: str | None = None
    create_date: datetime
    item_count: int = 0


class WatchlistDetailRead(BaseModel):
    """Detailed watchlist with nested items and movie metadata."""

    watchlist_id: int
    user_id: int
    watchlist_name: str
    notes: str | None = None
    create_date: datetime
    items: list[WatchlistItemRead] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Review Schemas
# ---------------------------------------------------------------------------
class ReviewCreateRequest(BaseModel):
    """Request body to create a movie review."""

    rating: int = Field(..., ge=1, le=5)
    review_text: str | None = Field(default=None, max_length=5000)
    platform_id: int | None = Field(default=None, ge=1)


class ReviewUpdateRequest(BaseModel):
    """Request body to update an existing review."""

    rating: int = Field(..., ge=1, le=5)
    review_text: str | None = Field(default=None, max_length=5000)
    platform_id: int | None = Field(default=None, ge=1)


class ReviewRead(BaseModel):
    """Review response model."""

    review_id: int
    user_id: int
    username: str
    movie_id: int
    platform_id: int | None = None
    platform_name: str | None = None
    rating: float
    review_text: str | None = None
    reviewed_on: datetime
