"""
Юніт-тести для app/security/challenge_store.py

Перевіряють:
- генерацію та одноразове використання challenge
- TTL (протухання)
- прив'язку challenge до terminal_id
- паралельну безпеку (threading)
- cleanup_expired()
"""
import time
import threading

import pytest

import app.security.challenge_store as cs
from app.security.challenge_store import (
    generate_challenge,
    consume_challenge,
    cleanup_expired,
    CHALLENGE_TTL_SECONDS,
)


@pytest.fixture(autouse=True)
def clear_store():
    """Очищаємо глобальний словник перед кожним тестом."""
    with cs._lock:
        cs._challenges.clear()
    yield
    with cs._lock:
        cs._challenges.clear()


# ─── generate_challenge ───────────────────────────────────────────────────────

class TestGenerateChallenge:
    def test_returns_non_empty_string(self):
        token = generate_challenge(terminal_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_two_challenges_are_unique(self):
        t1 = generate_challenge(1)
        t2 = generate_challenge(1)
        assert t1 != t2

    def test_challenge_stored_in_dict(self):
        token = generate_challenge(terminal_id=5)
        with cs._lock:
            assert token in cs._challenges
            stored_tid, _ = cs._challenges[token]
            assert stored_tid == 5

    def test_challenge_uses_urlsafe_chars(self):
        for _ in range(20):
            token = generate_challenge(1)
            # token_urlsafe може містити -, _ але не + або /
            assert "+" not in token
            assert "/" not in token


# ─── consume_challenge — happy path ──────────────────────────────────────────

class TestConsumeChallengValid:
    def test_valid_consume_returns_true(self):
        token = generate_challenge(terminal_id=1)
        assert consume_challenge(token, terminal_id=1) is True

    def test_challenge_removed_after_consume(self):
        token = generate_challenge(terminal_id=1)
        consume_challenge(token, terminal_id=1)
        with cs._lock:
            assert token not in cs._challenges

    def test_different_terminals_independent(self):
        t1 = generate_challenge(terminal_id=1)
        t2 = generate_challenge(terminal_id=2)
        assert consume_challenge(t1, terminal_id=1) is True
        assert consume_challenge(t2, terminal_id=2) is True


# ─── consume_challenge — one-time use ────────────────────────────────────────

class TestChallengeOneTimeUse:
    def test_replay_returns_false(self):
        token = generate_challenge(terminal_id=1)
        assert consume_challenge(token, 1) is True
        assert consume_challenge(token, 1) is False  # повторне — replay attack

    def test_unknown_token_returns_false(self):
        assert consume_challenge("nonexistent-token", terminal_id=1) is False

    def test_empty_token_returns_false(self):
        assert consume_challenge("", terminal_id=1) is False


# ─── consume_challenge — terminal_id mismatch ────────────────────────────────

class TestChallengeTerminalMismatch:
    def test_wrong_terminal_id_returns_false(self):
        token = generate_challenge(terminal_id=1)
        assert consume_challenge(token, terminal_id=2) is False

    def test_wrong_terminal_does_not_consume(self):
        """Після неправильного terminal_id challenge має бути вже видалений з магазину."""
        token = generate_challenge(terminal_id=1)
        # consume_challenge видаляє запис незалежно від результату (pop)
        consume_challenge(token, terminal_id=99)
        # тому правильний термінал вже не зможе його використати
        assert consume_challenge(token, terminal_id=1) is False


# ─── TTL / expiry ─────────────────────────────────────────────────────────────

class TestChallengeTTL:
    def test_fresh_challenge_not_expired(self):
        token = generate_challenge(terminal_id=1)
        assert consume_challenge(token, terminal_id=1) is True

    def test_expired_challenge_returns_false(self, monkeypatch):
        """Підміняємо time.time() так, щоб challenge виглядав протухлим."""
        token = generate_challenge(terminal_id=1)

        # Фіксуємо «майбутнє» де challenge вже старий
        future = time.time() + CHALLENGE_TTL_SECONDS + 1
        monkeypatch.setattr(cs, "time", type("FakeTime", (), {"time": staticmethod(lambda: future)})())

        assert consume_challenge(token, terminal_id=1) is False

    def test_ttl_constant_is_reasonable(self):
        assert 10 <= CHALLENGE_TTL_SECONDS <= 120, (
            f"TTL={CHALLENGE_TTL_SECONDS}с виглядає неправильним"
        )


# ─── cleanup_expired ──────────────────────────────────────────────────────────

class TestCleanupExpired:
    def test_cleanup_removes_old_entries(self, monkeypatch):
        token = generate_challenge(terminal_id=1)

        # Помічаємо entry як дуже старе (2× TTL)
        with cs._lock:
            tid, _ = cs._challenges[token]
            cs._challenges[token] = (tid, time.time() - CHALLENGE_TTL_SECONDS * 3)

        cleanup_expired()

        with cs._lock:
            assert token not in cs._challenges

    def test_cleanup_keeps_fresh_entries(self):
        token = generate_challenge(terminal_id=1)
        cleanup_expired()
        with cs._lock:
            assert token in cs._challenges

    def test_cleanup_does_not_crash_on_empty_store(self):
        cleanup_expired()  # не повинен кидати виключення


# ─── Thread safety ────────────────────────────────────────────────────────────

class TestChallengeThreadSafety:
    def test_concurrent_consume_only_one_wins(self):
        """100 потоків намагаються consume одного challenge — лише один має отримати True."""
        token = generate_challenge(terminal_id=1)
        results = []
        lock = threading.Lock()

        def try_consume():
            result = consume_challenge(token, terminal_id=1)
            with lock:
                results.append(result)

        threads = [threading.Thread(target=try_consume) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results.count(True) == 1
        assert results.count(False) == 99

    def test_concurrent_generate_all_unique(self):
        """50 потоків генерують challenges — всі токени мають бути унікальні."""
        tokens = []
        lock = threading.Lock()

        def gen():
            t = generate_challenge(terminal_id=1)
            with lock:
                tokens.append(t)

        threads = [threading.Thread(target=gen) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(tokens) == len(set(tokens)), "Знайдено дублікати challenge"
