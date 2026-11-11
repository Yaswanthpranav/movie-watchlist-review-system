"""Watchlist CRUD, authorization, and explicit atomic transaction tests."""

from fastapi.testclient import TestClient


def test_watchlist_full_crud_flow(client: TestClient, user1_auth) -> None:
    """Owner can create, list, view, add items, update status, remove items, and delete watchlist."""
    _, headers = user1_auth
    movies = client.get("/movies").json()["items"]
    m1_id = movies[0]["movie_id"]
    m2_id = movies[1]["movie_id"]

    # Create watchlist using 'name' alias
    create_res = client.post(
        "/watchlists",
        json={"name": "Weekend Picks", "notes": "Top priorities"},
        headers=headers,
    )
    assert create_res.status_code == 201
    wl = create_res.json()
    wl_id = wl["watchlist_id"]
    assert wl["watchlist_name"] == "Weekend Picks"
    assert wl["notes"] == "Top priorities"

    # Add two items
    add1 = client.post(
        f"/watchlists/{wl_id}/items",
        json={"movie_id": m1_id},
        headers=headers,
    )
    assert add1.status_code == 201
    assert add1.json()["status"] == "PLANNED"

    add2 = client.post(
        f"/watchlists/{wl_id}/items",
        json={"movie_id": m2_id, "status": "WATCHING"},
        headers=headers,
    )
    assert add2.status_code == 201
    assert add2.json()["status"] == "WATCHING"

    # List user's watchlists shows item_count == 2
    list_res = client.get("/watchlists", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["item_count"] == 2

    # Get watchlist details includes nested movie info
    detail_res = client.get(f"/watchlists/{wl_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["items"]) == 2
    assert all("title" in item["movie"] for item in detail["items"])

    # Update item status
    patch_res = client.patch(
        f"/watchlists/{wl_id}/items/{m1_id}",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "COMPLETED"

    # Delete item
    del_item = client.delete(f"/watchlists/{wl_id}/items/{m2_id}", headers=headers)
    assert del_item.status_code == 204

    after_del = client.get(f"/watchlists/{wl_id}", headers=headers).json()
    assert len(after_del["items"]) == 1

    # Delete entire watchlist
    del_wl = client.delete(f"/watchlists/{wl_id}", headers=headers)
    assert del_wl.status_code == 204

    missing_wl = client.get(f"/watchlists/{wl_id}", headers=headers)
    assert missing_wl.status_code == 404


def test_watchlist_auth_not_found_and_validation(client: TestClient, user1_auth) -> None:
    """Unauthenticated requests return 401; missing resources return 404; invalid bodies return 422."""
    _, headers = user1_auth

    assert client.get("/watchlists").status_code == 401
    assert client.post("/watchlists", json={"name": "Anon"}).status_code == 401

    # Blank name -> 422
    assert (
        client.post("/watchlists", json={"name": "   "}, headers=headers).status_code
        == 422
    )

    # Missing watchlist -> 404
    assert client.get("/watchlists/999999", headers=headers).status_code == 404
    assert client.delete("/watchlists/999999", headers=headers).status_code == 404

    # Create valid watchlist, check missing item update/delete -> 404
    wl_id = client.post(
        "/watchlists", json={"watchlist_name": "Mine"}, headers=headers
    ).json()["watchlist_id"]
    assert (
        client.patch(
            f"/watchlists/{wl_id}/items/999999",
            json={"status": "COMPLETED"},
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/watchlists/{wl_id}/items/999999", headers=headers).status_code
        == 404
    )


def test_watchlist_with_items_explicit_transaction_atomicity(
    client: TestClient,
    user1_auth,
) -> None:
    """Explicit transaction endpoint creates all atomically or rolls back completely on failure."""
    _, headers = user1_auth
    movies = client.get("/movies").json()["items"]
    valid_m1 = movies[0]["movie_id"]
    valid_m2 = movies[1]["movie_id"]

    # Failure on second item must roll back the watchlist header creation too
    fail_res = client.post(
        "/watchlists/with-items",
        json={
            "watchlist_name": "Atomic Rollback List",
            "notes": "Should not persist",
            "items": [
                {"movie_id": valid_m1, "status": "PLANNED"},
                {"movie_id": 999999, "status": "COMPLETED"},
            ],
        },
        headers=headers,
    )
    assert fail_res.status_code == 409

    # Confirm zero watchlists were persisted
    user_lists = client.get("/watchlists", headers=headers).json()
    assert user_lists == []

    # Valid atomic creation succeeds with all items
    ok_res = client.post(
        "/watchlists/with-items",
        json={
            "watchlist_name": "Atomic Success List",
            "items": [
                {"movie_id": valid_m1, "status": "WATCHING"},
                {"movie_id": valid_m2, "status": "COMPLETED"},
            ],
        },
        headers=headers,
    )
    assert ok_res.status_code == 201
    assert len(ok_res.json()["items"]) == 2
