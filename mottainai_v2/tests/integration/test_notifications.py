"""Integration tests for notification endpoints."""
import pytest


class TestNotifications:
    def test_empty_notifications(self, auth_client):
        resp = auth_client.get("/api/v1/notifications/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_unread_count_zero_initially(self, auth_client):
        resp = auth_client.get("/api/v1/notifications/unread-count")
        assert resp.status_code == 200
        assert resp.json()["data"]["unread_count"] == 0

    def test_unauthenticated_access_denied(self, client):
        resp = client.get("/api/v1/notifications/")
        assert resp.status_code == 401
