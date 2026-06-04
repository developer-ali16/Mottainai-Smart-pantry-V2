"""Unit tests for security utilities."""
import pytest
from datetime import timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from tests.conftest import override_get_settings

settings = override_get_settings()


class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = hash_password("MyPassword1")
        assert hashed != "MyPassword1"

    def test_verify_correct_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("MyPassword1", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("WrongPass1", hashed) is False

    def test_two_hashes_differ(self):
        """bcrypt uses a random salt — same input must produce different hashes."""
        h1 = hash_password("Same1")
        h2 = hash_password("Same1")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_access_token(42, settings)
        payload = decode_access_token(token, settings)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_expired_token_raises(self):
        from fastapi import HTTPException
        token = create_access_token(1, settings, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token, settings)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_tampered_token_raises(self):
        from fastapi import HTTPException
        token = create_access_token(1, settings) + "tampered"
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token, settings)
        assert exc_info.value.status_code == 401
