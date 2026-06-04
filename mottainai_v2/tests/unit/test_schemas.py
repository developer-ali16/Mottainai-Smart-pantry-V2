"""Unit tests for Pydantic schema validation."""
import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.schemas.user import UserRegister
from app.schemas.pantry_item import PantryItemCreate


class TestUserRegisterSchema:
    def test_valid_registration(self):
        u = UserRegister(full_name="Jane Doe", email="jane@example.com", password="Secure1pass")
        assert u.full_name == "Jane Doe"

    def test_name_normalised_to_title_case(self):
        u = UserRegister(full_name="  john   doe  ", email="j@example.com", password="Secure1pass")
        assert u.full_name == "John Doe"

    def test_weak_password_no_uppercase(self):
        with pytest.raises(ValidationError, match="uppercase"):
            UserRegister(full_name="A B", email="a@b.com", password="nouppercase1")

    def test_weak_password_no_digit(self):
        with pytest.raises(ValidationError, match="digit"):
            UserRegister(full_name="A B", email="a@b.com", password="NoDigitPass")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserRegister(full_name="A B", email="a@b.com", password="Ab1")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegister(full_name="A B", email="not-an-email", password="Secure1pass")


class TestPantryItemCreateSchema:
    def _valid_payload(self, **overrides):
        defaults = {
            "item_name": "Milk",
            "quantity": 2.0,
            "unit": "liter",
            "expiry_date": date.today() + timedelta(days=5),
        }
        defaults.update(overrides)
        return defaults

    def test_valid_item(self):
        item = PantryItemCreate(**self._valid_payload())
        assert item.item_name == "milk"   # lowercased

    def test_past_expiry_rejected(self):
        with pytest.raises(ValidationError, match="past"):
            PantryItemCreate(**self._valid_payload(expiry_date=date.today() - timedelta(days=1)))

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            PantryItemCreate(**self._valid_payload(quantity=0))

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            PantryItemCreate(**self._valid_payload(quantity=-1))
