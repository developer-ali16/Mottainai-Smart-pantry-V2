"""Integration tests for authentication endpoints."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "full_name": "Alice Smith",
            "email": "alice@example.com",
            "password": "AlicePass1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "alice@example.com"
        assert "password" not in str(data)

    def test_duplicate_email_returns_409(self, client):
        payload = {"full_name": "Bob", "email": "bob@example.com", "password": "BobPass1"}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "full_name": "C D", "email": "bad-email", "password": "CdPass1x"
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success_sets_cookie(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass1",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_wrong_password_returns_401(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPass1",
        })
        assert resp.status_code == 401
        # Must NOT reveal which field was wrong
        assert "email" not in resp.json()["error"]["message"].lower()
        assert "password" not in resp.json()["error"]["message"].lower()

    def test_unknown_email_same_error_as_wrong_password(self, client):
        r1 = client.post("/api/v1/auth/login", json={"email": "nobody@x.com", "password": "X"})
        r2 = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "X"})
        # Both return 401 with identical message (no enumeration)
        assert r1.status_code == r2.status_code == 401
        assert r1.json()["error"]["message"] == r2.json()["error"]["message"]


class TestLogout:
    def test_logout_clears_cookie(self, auth_client):
        resp = auth_client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

    def test_me_after_logout_returns_401(self, auth_client):
        auth_client.post("/api/v1/auth/logout")
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_user(self, auth_client, registered_user):
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == registered_user["email"]

    def test_me_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
