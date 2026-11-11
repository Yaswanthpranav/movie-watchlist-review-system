"""Movie catalog, lookup, rating aggregation, and ranking tests."""

from fastapi.testclient import TestClient


def test_health_and_lookup_endpoints(client: TestClient) -> None:
    """Health check and genre/language/platform lookups succeed."""
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "connected"}

    genres = client.get("/genres")
    assert genres.status_code == 200
    assert len(genres.json()) == 4
    assert {g["genre_name"] for g in genres.json()} == {
        "Sci-Fi",
        "Drama",
        "Thriller",
        "Animation",
    }

    languages = client.get("/languages")
    assert languages.status_code == 200
    assert len(languages.json()) == 3

    platforms = client.get("/platforms")
    assert platforms.status_code == 200
    assert len(platforms.json()) == 3


def test_list_movies_filters_pagination_and_sorting(client: TestClient) -> None:
    """Movie catalog filtering, sorting, and pagination return expected results."""
    # Unfiltered catalog
    res = client.get("/movies")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    assert len(data["items"]) == 4

    # Search by title
    search_res = client.get("/movies", params={"search": "parasite"})
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert search_res.json()["items"][0]["title"] == "Parasite"

    # Filter by year
    year_res = client.get("/movies", params={"year": 2014})
    assert year_res.status_code == 200
    assert [m["title"] for m in year_res.json()["items"]] == ["Interstellar"]

    # Filter by genre_id and language_id
    genres = {g["genre_name"]: g["genre_id"] for g in client.get("/genres").json()}
    langs = {l["language_name"]: l["language_id"] for l in client.get("/languages").json()}
    platforms = {
        p["streaming_platform_name"]: p["streaming_platform_id"]
        for p in client.get("/platforms").json()
    }

    scifi_res = client.get("/movies", params={"genre_id": genres["Sci-Fi"]})
    assert scifi_res.status_code == 200
    assert {m["title"] for m in scifi_res.json()["items"]} == {
        "Inception",
        "Interstellar",
    }

    ko_res = client.get("/movies", params={"language_id": langs["Korean"]})
    assert ko_res.status_code == 200
    assert [m["title"] for m in ko_res.json()["items"]] == ["Parasite"]

    mubi_res = client.get("/movies", params={"platform_id": platforms["MUBI"]})
    assert mubi_res.status_code == 200
    assert [m["title"] for m in mubi_res.json()["items"]] == ["Parasite"]

    # Sorting by year_desc and pagination
    page1 = client.get(
        "/movies", params={"sort": "year_desc", "page": 1, "page_size": 2}
    )
    assert page1.status_code == 200
    assert page1.json()["total"] == 4
    assert [m["title"] for m in page1.json()["items"]] == ["Parasite", "Interstellar"]

    page2 = client.get(
        "/movies", params={"sort": "year_desc", "page": 2, "page_size": 2}
    )
    assert page2.status_code == 200
    assert [m["title"] for m in page2.json()["items"]] == ["Inception", "Spirited Away"]


def test_movie_detail_and_not_found(client: TestClient) -> None:
    """GET /movies/{id} returns full details or 404 when missing."""
    movies = client.get("/movies").json()["items"]
    inception = next(m for m in movies if m["title"] == "Inception")

    detail = client.get(f"/movies/{inception['movie_id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["title"] == "Inception"
    assert body["language"]["language_name"] == "English"
    assert {g["genre_name"] for g in body["genres"]} == {"Sci-Fi", "Thriller"}
    assert {p["streaming_platform_name"] for p in body["platforms"]} == {
        "Netflix",
        "Amazon Prime Video",
    }
    assert body["average_rating"] is None
    assert body["review_count"] == 0

    missing = client.get("/movies/999999")
    assert missing.status_code == 404


def test_average_rating_matches_manual_computation_and_top_rated_rank(
    client: TestClient,
    register_and_login,
) -> None:
    """API average_rating equals manual average across multiple users & movies, and RANK() OVER orders top-rated."""
    _, h1 = register_and_login("rater1", "r1@example.com")
    _, h2 = register_and_login("rater2", "r2@example.com")
    _, h3 = register_and_login("rater3", "r3@example.com")

    movies = {m["title"]: m["movie_id"] for m in client.get("/movies").json()["items"]}
    inc_id = movies["Inception"]
    par_id = movies["Parasite"]

    # Inception ratings: 5, 4, 4 => manual avg = 13 / 3 = 4.33
    ratings_inc = [5, 4, 4]
    for headers, rating in zip([h1, h2, h3], ratings_inc):
        resp = client.post(
            f"/movies/{inc_id}/reviews",
            json={"rating": rating, "review_text": f"Rated {rating}"},
            headers=headers,
        )
        assert resp.status_code == 201

    # Parasite ratings: 5, 5 => manual avg = 5.0
    for headers in [h1, h2]:
        resp = client.post(
            f"/movies/{par_id}/reviews",
            json={"rating": 5, "review_text": "Masterpiece"},
            headers=headers,
        )
        assert resp.status_code == 201

    expected_inc_avg = round(sum(ratings_inc) / len(ratings_inc), 2)

    detail_inc = client.get(f"/movies/{inc_id}").json()
    assert detail_inc["review_count"] == 3
    assert detail_inc["average_rating"] == expected_inc_avg

    list_res = client.get("/movies", params={"min_rating": 4.5}).json()
    assert [m["title"] for m in list_res["items"]] == ["Parasite"]
    assert list_res["items"][0]["average_rating"] == 5.0
    assert list_res["items"][0]["review_count"] == 2

    # Window function RANK() OVER endpoint
    top_res = client.get("/movies/top-rated", params={"limit": 5, "min_reviews": 1})
    assert top_res.status_code == 200
    top = top_res.json()
    assert len(top) == 2
    assert top[0]["rank"] == 1
    assert top[0]["title"] == "Parasite"
    assert top[1]["rank"] == 2
    assert top[1]["title"] == "Inception"
    assert top[1]["average_rating"] == expected_inc_avg


def test_movies_validation_errors_return_422(client: TestClient) -> None:
    """Invalid query parameters return 422 Unprocessable Entity."""
    bad_page = client.get("/movies", params={"page": 0})
    assert bad_page.status_code == 422

    bad_min_rating = client.get("/movies", params={"min_rating": 6.0})
    assert bad_min_rating.status_code == 422

    bad_sort = client.get("/movies", params={"sort": "invalid_sort"})
    assert bad_sort.status_code == 422


def test_normalize_database_url_targets_psycopg2() -> None:
    """postgres:// and postgresql:// normalize to postgresql+psycopg2:// while sqlite:// is rejected."""
    import pytest

    from app.database import _normalize_database_url

    assert (
        _normalize_database_url(" postgres://user:pass@host:5432/postgres ")
        == "postgresql+psycopg2://user:pass@host:5432/postgres"
    )
    assert (
        _normalize_database_url("postgresql://user:pass@host:5432/postgres")
        == "postgresql+psycopg2://user:pass@host:5432/postgres"
    )
    with pytest.raises(ValueError, match="PostgreSQL"):
        _normalize_database_url("sqlite:///./cinetrack.db")
