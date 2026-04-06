"""
Юніт-тести для app/core/security.py та app/core/time.py
"""
import os
import time
from datetime import datetime, timezone, timedelta

import pytest
from jose import jwt

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-32chars")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ADMIN_PASSWORD", "testpassword123")

from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.core.time import ensure_utc, to_warsaw, to_utc, local_date_str, WARSAW


# ─── hash_password / verify_password ─────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("secret123")
        assert h != "secret123"

    def test_hash_starts_with_bcrypt_prefix(self):
        h = hash_password("secret123")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_verify_correct_password(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("mypassword")
        assert verify_password("wrongpassword", h) is False

    def test_verify_empty_password_fails(self):
        h = hash_password("mypassword")
        assert verify_password("", h) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt використовує salt — хеші мають бути різними."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True

    def test_unicode_password(self):
        h = hash_password("пароль_123")
        assert verify_password("пароль_123", h) is True
        assert verify_password("parol_123", h) is False


# ─── create_access_token ──────────────────────────────────────────────────────

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token("admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_parts(self):
        token = create_access_token("admin")
        assert len(token.split(".")) == 3  # header.payload.signature

    def test_subject_in_payload(self):
        token = create_access_token("testuser")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        assert payload["sub"] == "testuser"

    def test_expiry_present_in_payload(self):
        token = create_access_token("admin")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        assert "exp" in payload

    def test_token_expires_in_future(self):
        token = create_access_token("admin")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        assert payload["exp"] > time.time()

    def test_custom_expiry_minutes(self):
        token = create_access_token("admin", expires_minutes=120)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        # Перевіряємо що exp приблизно через 120 хвилин
        expected_exp = time.time() + 120 * 60
        assert abs(payload["exp"] - expected_exp) < 5

    def test_extra_fields_in_payload(self):
        token = create_access_token("admin", extra={"role": "admin", "user_id": 42})
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        assert payload["role"] == "admin"
        assert payload["user_id"] == 42

    def test_wrong_secret_fails_decode(self):
        from jose import JWTError
        token = create_access_token("admin")
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret", algorithms=[settings.jwt_alg])

    def test_expired_token_fails_decode(self):
        from jose import ExpiredSignatureError
        token = create_access_token("admin", expires_minutes=-1)
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


# ─── core/time.py ─────────────────────────────────────────────────────────────

class TestEnsureUtc:
    def test_none_returns_now(self):
        before = datetime.now(timezone.utc)
        result = ensure_utc(None)
        after = datetime.now(timezone.utc)
        assert before <= result <= after
        assert result.tzinfo is not None

    def test_naive_treated_as_warsaw(self):
        naive = datetime(2024, 6, 1, 12, 0, 0)
        result = ensure_utc(naive)
        # Warsaw UTC+2 влітку → 12:00 Warsaw = 10:00 UTC
        assert result.tzinfo == timezone.utc
        assert result.hour == 10

    def test_utc_aware_preserved(self):
        dt = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(dt)
        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_warsaw_aware_converted(self):
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=WARSAW)
        result = ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result.hour == 10


class TestToWarsaw:
    def test_utc_to_warsaw_summer(self):
        dt = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = to_warsaw(dt)
        assert result.hour == 12  # UTC+2 влітку

    def test_utc_to_warsaw_winter(self):
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = to_warsaw(dt)
        assert result.hour == 11  # UTC+1 взимку

    def test_naive_treated_as_utc(self):
        naive = datetime(2024, 6, 1, 10, 0, 0)
        result = to_warsaw(naive)
        assert result.hour == 12

    def test_result_has_warsaw_timezone(self):
        dt = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = to_warsaw(dt)
        assert result.tzinfo == WARSAW


class TestToUtc:
    def test_naive_preserved_as_utc(self):
        naive = datetime(2024, 6, 1, 10, 0, 0)
        result = to_utc(naive)
        assert result.tzinfo == timezone.utc
        assert result.hour == 10

    def test_warsaw_aware_converted(self):
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=WARSAW)
        result = to_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result.hour == 10

    def test_utc_aware_unchanged(self):
        dt = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
        result = to_utc(dt)
        assert result == dt


class TestLocalDateStr:
    def test_utc_midnight_winter(self):
        """00:00 UTC взимку = 01:00 Варшава — та ж дата."""
        dt = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        assert local_date_str(dt) == "2024-01-15"

    def test_utc_night_rolls_to_next_day(self):
        """23:30 UTC влітку = 01:30 наступного дня у Варшаві."""
        dt = datetime(2024, 6, 1, 23, 30, 0, tzinfo=timezone.utc)
        assert local_date_str(dt) == "2024-06-02"

    def test_format_is_iso(self):
        dt = datetime(2024, 3, 5, 10, 0, 0, tzinfo=timezone.utc)
        result = local_date_str(dt)
        assert len(result) == 10
        assert result[4] == "-" and result[7] == "-"
