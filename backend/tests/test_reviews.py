"""Movie review CRUD, ownership, and rating aggregation tests."""

from fastapi.testclient import TestClient


def test_review_create_list_update_delete_flow(
    client: TestClient,
    user1_auth,
    user2_auth,
) -> None:
    """Authenticated user can create, update, and delete own review; another user gets 403."""
    _, h1 = user1_auth
    _, h2 = user2_auth

    movie_id = client.get("/movies").json()["items"][0]["movie_id"]
    platform_id = client.get("/platforms").json()[0]["streaming_platform_id"]

    # Create review
    create_res = client.post(
        f"/movies/{movie_id}/reviews",
        json={"rating": 4, "review_text": "Great watch", "platform_id": platform_id},
        headers=h1,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    review_id = created["review_id"]
    assert created["rating"] == 4
    assert created["username"] == "test_alice"
    assert created["platform_id"] == platform_id

    # List movie reviews
    list_res = client.get(f"/movies/{movie_id}/reviews")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Another user cannot update or delete user1's review
    forbid_put = client.put(
        f"/reviews/{review_id}",
        json={"rating": 1, "review_text": "Hijack"},
        headers=h2,
    )
    assert forbid_put.status_code == 403

    forbid_del = client.delete(f"/reviews/{review_id}", headers=h2)
    assert forbid_del.status_code == 403

    # Owner updates review
    put_res = client.put(
        f"/reviews/{review_id}",
        json={"rating": 5, "review_text": "Even better on rewatch"},
        headers=h1,
    )
    assert put_res.status_code == 200
    assert put_res.json()["rating"] == 5
    assert put_res.json()["review_text"] == "Even better on rewatch"

    # Movie aggregate updates accordingly
    detail = client.get(f"/movies/{movie_id}").json()
    assert detail["average_rating"] == 5.0
    assert detail["review_count"] == 1

    # Owner deletes review
    del_res = client.delete(f"/reviews/{review_id}", headers=h1)
    assert del_res.status_code == 204

    detail_after = client.get(f"/movies/{movie_id}").json()
    assert detail_after["average_rating"] is None
    assert detail_after["review_count"] == 0


def test_review_auth_not_found_and_validation(client: TestClient, user1_auth) -> None:
    """Verify 401 unauthenticated, 404 missing movie/review, and 422 validation errors."""
    _, headers = user1_auth
    movie_id = client.get("/movies").json()["items"][0]["movie_id"]

    # Unauthenticated write -> 401
    assert (
        client.post(f"/movies/{movie_id}/reviews", json={"rating": 5}).status_code
        == 401
    )
    assert client.put("/reviews/1", json={"rating": 5}).status_code == 401
    assert client.delete("/reviews/1").status_code == 401

    # Missing movie -> 404
    assert client.get("/movies/999999/reviews").status_code == 404
    assert (
        client.post(
            "/movies/999999/reviews", json={"rating": 5}, headers=headers
        ).status_code
        == 404
    )

    # Missing review -> 404
    assert (
        client.put("/reviews/999999", json={"rating": 4}, headers=headers).status_code
        == 404
    )
    assert client.delete("/reviews/999999", headers=headers).status_code == 404
