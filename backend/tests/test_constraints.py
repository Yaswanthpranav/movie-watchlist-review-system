"""Database integrity constraint and ownership enforcement tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Language, Movie, MoviePlatform, Review, Watchlist, WatchlistItem


def test_duplicate_watchlist_item_rejected_409(client: TestClient, user1_auth) -> None:
    """Adding the same movie twice to the same watchlist fails with 409 Conflict."""
    _, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]
    wl_id = client.post(
        "/watchlists", json={"watchlist_name": "Dup Test"}, headers=headers
    ).json()["watchlist_id"]

    first = client.post(
        f"/watchlists/{wl_id}/items", json={"movie_id": movie_id}, headers=headers
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/watchlists/{wl_id}/items", json={"movie_id": movie_id}, headers=headers
    )
    assert duplicate.status_code == 409


def test_duplicate_review_by_same_user_rejected_409(
    client: TestClient, user1_auth
) -> None:
    """Posting a second review by the same user on the same movie fails with 409 Conflict."""
    _, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]

    first = client.post(
        f"/movies/{movie_id}/reviews",
        json={"rating": 5, "review_text": "First review"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/movies/{movie_id}/reviews",
        json={"rating": 3, "review_text": "Duplicate review"},
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_rating_out_of_range_rejected_api_and_db(
    client: TestClient,
    db_session: Session,
    user1_auth,
) -> None:
    """Ratings 0 and 6 are rejected both by Pydantic (422) and DB CHECK constraint (IntegrityError)."""
    user, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]

    # API layer validation -> 422
    for invalid_rating in (0, 6):
        res = client.post(
            f"/movies/{movie_id}/reviews",
            json={"rating": invalid_rating},
            headers=headers,
        )
        assert res.status_code == 422

    # Direct DB layer CHECK constraint enforcement -> IntegrityError
    for invalid_rating in (0, 6):
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.add(
                    Review(
                        user_id=user["user_id"],
                        movie_id=movie_id,
                        rating=invalid_rating,
                    )
                )
                db_session.flush()


def test_duplicate_username_and_email_rejected_409(client: TestClient) -> None:
    """Duplicate username or duplicate email both fail with 409 Conflict."""
    first = client.post(
        "/auth/register",
        json={
            "username": "unique_user",
            "email": "unique@example.com",
            "password": "password123",
        },
    )
    assert first.status_code == 201

    dup_username = client.post(
        "/auth/register",
        json={
            "username": "unique_user",
            "email": "different@example.com",
            "password": "password123",
        },
    )
    assert dup_username.status_code == 409

    dup_email = client.post(
        "/auth/register",
        json={
            "username": "different_user",
            "email": "unique@example.com",
            "password": "password123",
        },
    )
    assert dup_email.status_code == 409


def test_invalid_foreign_keys_rejected_api_and_db(
    client: TestClient,
    db_session: Session,
    user1_auth,
) -> None:
    """Invalid foreign keys are rejected by the DB and translated to 409 at the API layer."""
    _, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]
    wl_id = client.post(
        "/watchlists", json={"watchlist_name": "FK Test"}, headers=headers
    ).json()["watchlist_id"]

    # API layer: invalid movie_id FK in watchlist item -> 409
    bad_item_fk = client.post(
        f"/watchlists/{wl_id}/items",
        json={"movie_id": 999999},
        headers=headers,
    )
    assert bad_item_fk.status_code == 409

    # API layer: invalid platform_id FK in review -> 409
    bad_platform_fk = client.post(
        f"/movies/{movie_id}/reviews",
        json={"rating": 4, "platform_id": 999999},
        headers=headers,
    )
    assert bad_platform_fk.status_code == 409

    # Direct DB layer FK enforcement
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                Movie(
                    title="Invalid Lang Movie",
                    release_yr=2024,
                    duration=100,
                    language_id=999999,
                )
            )
            db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                Watchlist(user_id=999999, watchlist_name="Orphan Watchlist")
            )
            db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(MoviePlatform(movie_id=movie_id, platform_id=999999))
            db_session.flush()


def test_invalid_watchlist_status_rejected_api_and_db(
    client: TestClient,
    db_session: Session,
    user1_auth,
) -> None:
    """Invalid watchlist status is rejected both by Pydantic (422) and DB CHECK constraint."""
    _, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]
    wl_id = client.post(
        "/watchlists", json={"watchlist_name": "Status Test"}, headers=headers
    ).json()["watchlist_id"]

    # API layer validation -> 422 on POST and PATCH
    for invalid_status in ("Dropped", "Want to Watch"):
        bad_post = client.post(
            f"/watchlists/{wl_id}/items",
            json={"movie_id": movie_id, "status": invalid_status},
            headers=headers,
        )
        assert bad_post.status_code == 422

    client.post(
        f"/watchlists/{wl_id}/items",
        json={"movie_id": movie_id, "status": "PLANNED"},
        headers=headers,
    )
    bad_patch = client.patch(
        f"/watchlists/{wl_id}/items/{movie_id}",
        json={"status": "Abandoned"},
        headers=headers,
    )
    assert bad_patch.status_code == 422

    # Direct DB layer CHECK constraint enforcement -> IntegrityError
    other_movie_id = client.get("/movies").json()["items"][1]["movie_id"]
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(
                WatchlistItem(
                    watchlist_id=wl_id,
                    movie_id=other_movie_id,
                    status="Dropped",
                )
            )
            db_session.flush()


def test_duplicate_watchlist_name_for_same_user_rejected_409(
    client: TestClient,
    user1_auth,
) -> None:
    """Creating two watchlists with the same name for one user fails with 409 Conflict."""
    _, headers = user1_auth
    first = client.post(
        "/watchlists",
        json={"watchlist_name": "Sci-Fi Vault"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/watchlists",
        json={"watchlist_name": "Sci-Fi Vault"},
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_non_positive_movie_duration_rejected_db(db_session: Session) -> None:
    """Movie duration <= 0 is rejected by DB CHECK constraint."""
    lang = db_session.scalar(select(Language).limit(1))
    assert lang is not None

    for bad_duration in (0, -90):
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.add(
                    Movie(
                        title="Bad Duration",
                        release_yr=2024,
                        duration=bad_duration,
                        language_id=lang.language_id,
                    )
                )
                db_session.flush()


def test_another_users_watchlist_forbidden_403(
    client: TestClient,
    user1_auth,
    user2_auth,
) -> None:
    """Accessing or modifying another user's watchlist returns 403 Forbidden."""
    _, h1 = user1_auth
    _, h2 = user2_auth

    movie_id = client.get("/movies").json()["items"][0]["movie_id"]
    wl_id = client.post(
        "/watchlists", json={"watchlist_name": "Alice Private"}, headers=h1
    ).json()["watchlist_id"]
    client.post(
        f"/watchlists/{wl_id}/items", json={"movie_id": movie_id}, headers=h1
    )

    assert client.get(f"/watchlists/{wl_id}", headers=h2).status_code == 403
    assert (
        client.post(
            f"/watchlists/{wl_id}/items",
            json={"movie_id": movie_id},
            headers=h2,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/watchlists/{wl_id}/items/{movie_id}",
            json={"status": "COMPLETED"},
            headers=h2,
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/watchlists/{wl_id}/items/{movie_id}", headers=h2
        ).status_code
        == 403
    )
    assert client.delete(f"/watchlists/{wl_id}", headers=h2).status_code == 403
