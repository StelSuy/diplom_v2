"""
Юніт-тести для app/security/rate_limit.py

Перевіряють:
- пропускає запити до ліміту
- блокує 429 після перевищення
- вікно ковзне: старі записи не рахуються
- різні IP незалежні
- cleanup_all()
"""
import time

import pytest
from fastapi import HTTPException

import app.security.rate_limit as rl
from app.security.rate_limit import check_rate_limit, cleanup_all, MAX_REQUESTS_PER_WINDOW, WINDOW_SECONDS


# ─── Фіктивний Request ───────────────────────────────────────────────────────

class FakeClient:
    def __init__(self, host: str):
        self.host = host


class FakeRequest:
    def __init__(self, ip: str = "127.0.0.1"):
        self.client = FakeClient(ip)


@pytest.fixture(autouse=True)
def clear_rate_limit_store():
    """Скидаємо глобальний лічильник перед кожним тестом."""
    with rl._lock:
        rl._counts.clear()
    yield
    with rl._lock:
        rl._counts.clear()


# ─── Базова поведінка ─────────────────────────────────────────────────────────

class TestRateLimitBasic:
    def test_single_request_passes(self):
        check_rate_limit(FakeRequest("1.2.3.4"))  # не повинен кидати

    def test_requests_up_to_limit_pass(self):
        req = FakeRequest("10.0.0.1")
        for _ in range(MAX_REQUESTS_PER_WINDOW):
            check_rate_limit(req)

    def test_request_over_limit_raises_429(self):
        req = FakeRequest("10.0.0.2")
        for _ in range(MAX_REQUESTS_PER_WINDOW):
            check_rate_limit(req)
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(req)
        assert exc_info.value.status_code == 429

    def test_429_detail_message_present(self):
        req = FakeRequest("10.0.0.3")
        for _ in range(MAX_REQUESTS_PER_WINDOW):
            check_rate_limit(req)
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(req)
        assert exc_info.value.detail  # повідомлення не порожнє

    def test_limit_constant_is_reasonable(self):
        assert 10 <= MAX_REQUESTS_PER_WINDOW <= 1000

    def test_window_constant_is_reasonable(self):
        assert 10 <= WINDOW_SECONDS <= 3600


# ─── Ізоляція між IP ─────────────────────────────────────────────────────────

class TestRateLimitIsolation:
    def test_different_ips_independent(self):
        """Перевищення ліміту для одного IP не впливає на інший."""
        req_a = FakeRequest("192.168.1.1")
        req_b = FakeRequest("192.168.1.2")

        for _ in range(MAX_REQUESTS_PER_WINDOW):
            check_rate_limit(req_a)

        with pytest.raises(HTTPException):
            check_rate_limit(req_a)

        # IP B досі вільний
        check_rate_limit(req_b)  # не повинен кидати

    def test_ten_distinct_ips_all_pass(self):
        for i in range(10):
            check_rate_limit(FakeRequest(f"10.0.{i}.1"))


# ─── Ковзне вікно ─────────────────────────────────────────────────────────────

class TestRateLimitSlidingWindow:
    def test_old_timestamps_not_counted(self, monkeypatch):
        """Запити, старіші за WINDOW_SECONDS, не рахуються."""
        ip = "5.5.5.5"

        # Додаємо MAX записів у минулому (поза вікном)
        old_time = time.time() - WINDOW_SECONDS - 10
        with rl._lock:
            rl._counts[ip] = [old_time] * MAX_REQUESTS_PER_WINDOW

        # Новий запит — вікно вже порожнє, має пройти
        check_rate_limit(FakeRequest(ip))

    def test_mix_old_and_new_respects_limit(self, monkeypatch):
        """Частина записів стара, частина свіжа — тільки свіжі рахуються."""
        ip = "6.6.6.6"
        now = time.time()
        old_time = now - WINDOW_SECONDS - 5
        fresh_count = MAX_REQUESTS_PER_WINDOW - 1

        with rl._lock:
            rl._counts[ip] = [old_time] * 50 + [now] * fresh_count

        # Ще один запит — загалом fresh_count + 1 = MAX, має пройти
        check_rate_limit(FakeRequest(ip))


# ─── cleanup_all ─────────────────────────────────────────────────────────────

class TestCleanupAll:
    def test_cleanup_removes_stale_ip(self):
        ip = "9.9.9.9"
        old_time = time.time() - WINDOW_SECONDS - 60
        with rl._lock:
            rl._counts[ip] = [old_time] * 5

        cleanup_all()

        with rl._lock:
            assert ip not in rl._counts

    def test_cleanup_keeps_active_ip(self):
        ip = "8.8.8.8"
        check_rate_limit(FakeRequest(ip))
        cleanup_all()
        with rl._lock:
            assert ip in rl._counts

    def test_cleanup_on_empty_store_no_crash(self):
        cleanup_all()
