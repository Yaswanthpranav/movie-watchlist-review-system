"""SQLAlchemy 2.0 ORM models mirroring the live Supabase schema exactly."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Registered CineTrack user account ("user" is quoted in PostgreSQL)."""

    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    create_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    auth_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        unique=True,
        nullable=True,
    )

    watchlists: Mapped[list["Watchlist"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Language(Base):
    """Spoken language lookup table."""

    __tablename__ = "language"

    language_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(back_populates="language")


class Genre(Base):
    """Movie genre lookup table."""

    __tablename__ = "genre"

    genre_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    genre_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movie_genres: Mapped[list["MovieGenre"]] = relationship(
        back_populates="genre",
        cascade="all, delete-orphan",
    )


class StreamingPlatform(Base):
    """Streaming service lookup table."""

    __tablename__ = "streaming_platform"

    streaming_platform_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    streaming_platform_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    movie_platforms: Mapped[list["MoviePlatform"]] = relationship(
        back_populates="platform",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="platform")


class Movie(Base):
    """Movie catalog entry."""

    __tablename__ = "movie"
    __table_args__ = (
        CheckConstraint("duration > 0", name="movie_duration_check"),
    )

    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_yr: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    language_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("language.language_id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_rating: Mapped[str | None] = mapped_column(String(50), nullable=True)

    language: Mapped["Language"] = relationship(back_populates="movies")
    movie_genres: Mapped[list["MovieGenre"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )
    movie_platforms: Mapped[list["MoviePlatform"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )


class MovieGenre(Base):
    """Many-to-many junction table between movies and genres."""

    __tablename__ = "movie_genre"

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie.movie_id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("genre.genre_id", ondelete="CASCADE"),
        primary_key=True,
    )

    movie: Mapped["Movie"] = relationship(back_populates="movie_genres")
    genre: Mapped["Genre"] = relationship(back_populates="movie_genres")


class MoviePlatform(Base):
    """Many-to-many junction table between movies and streaming platforms."""

    __tablename__ = "movie_platform"

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie.movie_id", ondelete="CASCADE"),
        primary_key=True,
    )
    platform_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("streaming_platform.streaming_platform_id", ondelete="CASCADE"),
        primary_key=True,
    )

    movie: Mapped["Movie"] = relationship(back_populates="movie_platforms")
    platform: Mapped["StreamingPlatform"] = relationship(back_populates="movie_platforms")


class Watchlist(Base):
    """User-owned named watchlist."""

    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "watchlist_name", name="watchlist_user_name_unique"),
    )

    watchlist_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    watchlist_name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="watchlists")
    items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="watchlist",
        cascade="all, delete-orphan",
    )


class WatchlistItem(Base):
    """Movie entry inside a watchlist with viewing status."""

    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "movie_id", name="watchlist_movie_unique"),
        CheckConstraint(
            "status IN ('PLANNED', 'WATCHING', 'COMPLETED')",
            name="watchlist_status_check",
        ),
    )

    watchlist_item_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    watchlist_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist.watchlist_id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie.movie_id"),
        nullable=False,
    )
    added_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="PLANNED",
    )

    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")
    movie: Mapped["Movie"] = relationship(back_populates="watchlist_items")


class Review(Base):
    """User rating (1-5) and optional written review for a movie."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="reviews_user_movie_unique"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="reviews_rating_check"),
    )

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie.movie_id"),
        nullable=False,
    )
    platform_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("streaming_platform.streaming_platform_id"),
        nullable=True,
    )
    rating: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="reviews")
    movie: Mapped["Movie"] = relationship(back_populates="reviews")
    platform: Mapped["StreamingPlatform | None"] = relationship(back_populates="reviews")
