"""Integration tests for pantry endpoints."""
from datetime import date, timedelta
import pytest


FUTURE = (date.today() + timedelta(days=10)).isoformat()
SOON   = (date.today() + timedelta(days=2)).isoformat()


def _item(name="milk", expiry=None):
    return {
        "item_name": name,
        "quantity": 1.0,
        "unit": "liter",
        "expiry_date": expiry or FUTURE,
    }


class TestPantryCRUD:
    def test_create_item(self, auth_client):
        resp = auth_client.post("/api/v1/pantry/", json=_item())
        assert resp.status_code == 201
        assert resp.json()["data"]["item_name"] == "milk"

    def test_list_items_paginated(self, auth_client):
        for i in range(5):
            auth_client.post("/api/v1/pantry/", json=_item(f"item{i}"))
        resp = auth_client.get("/api/v1/pantry/?page=1&page_size=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 3
        assert "total" in body

    def test_get_item(self, auth_client):
        created = auth_client.post("/api/v1/pantry/", json=_item()).json()["data"]
        resp = auth_client.get(f"/api/v1/pantry/{created['id']}")
        assert resp.status_code == 200

    def test_update_item(self, auth_client):
        created = auth_client.post("/api/v1/pantry/", json=_item()).json()["data"]
        resp = auth_client.put(f"/api/v1/pantry/{created['id']}", json={"quantity": 3.5})
        assert resp.status_code == 200
        assert resp.json()["data"]["quantity"] == 3.5

    def test_delete_item_returns_204(self, auth_client):
        created = auth_client.post("/api/v1/pantry/", json=_item()).json()["data"]
        resp = auth_client.delete(f"/api/v1/pantry/{created['id']}")
        assert resp.status_code == 204

    def test_get_deleted_item_returns_404(self, auth_client):
        created = auth_client.post("/api/v1/pantry/", json=_item()).json()["data"]
        auth_client.delete(f"/api/v1/pantry/{created['id']}")
        resp = auth_client.get(f"/api/v1/pantry/{created['id']}")
        assert resp.status_code == 404

    def test_cannot_access_other_users_item(self, client, auth_client):
        # auth_client owns the item
        created = auth_client.post("/api/v1/pantry/", json=_item()).json()["data"]

        # Register and log in a second user
        client.post("/api/v1/auth/register", json={
            "full_name": "Evil User", "email": "evil@example.com", "password": "EvilPass1",
        })
        client.post("/api/v1/auth/login", json={"email": "evil@example.com", "password": "EvilPass1"})

        resp = client.get(f"/api/v1/pantry/{created['id']}")
        assert resp.status_code in (401, 404)


class TestPantrySummary:
    def test_summary_returns_counts(self, auth_client):
        auth_client.post("/api/v1/pantry/", json=_item("a", FUTURE))
        auth_client.post("/api/v1/pantry/", json=_item("b", SOON))
        resp = auth_client.get("/api/v1/pantry/summary")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "total_items" in body
        assert body["total_items"] >= 2


class TestPantryFilters:
    def test_expiring_soon_filter(self, auth_client):
        auth_client.post("/api/v1/pantry/", json=_item("soon_item", SOON))
        auth_client.post("/api/v1/pantry/", json=_item("far_item",  FUTURE))
        resp = auth_client.get("/api/v1/pantry/?expiring_soon=3")
        assert resp.status_code == 200
        names = [i["item_name"] for i in resp.json()["data"]]
        assert "soon_item" in names
        assert "far_item" not in names
