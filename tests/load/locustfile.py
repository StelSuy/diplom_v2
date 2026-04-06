"""
Locust load test — TimeTracker API
Запуск: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""
import uuid
import random
from locust import HttpUser, task, between, events


# ─── Тестові облікові дані ────────────────────────────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# API-ключ тестового терміналу (встановіть реальний з БД або вкажіть через env)
TERMINAL_API_KEY = "test-terminal-api-key"
TERMINAL_ID = 1

# Тестовий NFC UID (має існувати в БД для подій сканування)
TEST_NFC_UID = "TESTUID001"

DIRECTIONS = ["in", "out"]


# ─── Адміністратор (веб-панель) ───────────────────────────────────────────────
class AdminUser(HttpUser):
    """
    Імітує адміністратора: логін, перегляд співробітників,
    журналу аудиту, статистики, управління терміналами.
    """
    wait_time = between(1, 3)
    weight = 2  # менше адмінів, ніж терміналів

    token: str | None = None
    created_employee_ids: list = []

    def on_start(self):
        """Логін і отримання JWT-токена."""
        with self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            catch_response=True,
            name="/api/auth/login",
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
            else:
                resp.failure(f"Login failed: {resp.status_code} — {resp.text[:200]}")

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Найчастіші запити ─────────────────────────────────────────────────────

    @task(10)
    def health_check(self):
        """Перевірка живості — найлегший запит."""
        self.client.get("/health", name="/health")

    @task(6)
    def get_recent_scans(self):
        """Перегляд свіжих сканувань (головна сторінка панелі)."""
        self.client.get(
            "/api/stats/recent-scans",
            headers=self._headers(),
            name="/api/stats/recent-scans",
        )

    @task(5)
    def list_employees(self):
        """Список всіх співробітників."""
        self.client.get(
            "/api/employees/",
            headers=self._headers(),
            name="/api/employees/",
        )

    @task(4)
    def list_terminals(self):
        """Список терміналів."""
        self.client.get(
            "/api/terminals/",
            headers=self._headers(),
            name="/api/terminals/",
        )

    @task(3)
    def get_audit_log(self):
        """Журнал аудиту — важкий запит з пагінацією."""
        self.client.get(
            "/api/audit/log?limit=50&offset=0",
            headers=self._headers(),
            name="/api/audit/log",
        )

    @task(2)
    def get_employee_stats(self):
        """Статистика по конкретному співробітнику."""
        emp_id = random.choice(self.created_employee_ids) if self.created_employee_ids else 1
        self.client.get(
            f"/api/stats/employee/{emp_id}",
            headers=self._headers(),
            name="/api/stats/employee/{id}",
        )

    @task(2)
    def create_and_check_employee(self):
        """Створення нового співробітника та перегляд його картки."""
        uid = uuid.uuid4().hex[:8].upper()
        payload = {
            "full_name": f"Load Test {uid}",
            "nfc_uid": f"LT{uid}",
            "position": "Тестова посада",
            "comment": "Створено під час навантажувального тесту",
        }
        with self.client.post(
            "/api/employees/",
            json=payload,
            headers=self._headers(),
            catch_response=True,
            name="/api/employees/ [create]",
        ) as resp:
            if resp.status_code in (200, 201):
                emp_id = resp.json().get("id")
                if emp_id:
                    self.created_employee_ids.append(emp_id)
                    # Одразу перевіряємо картку
                    self.client.get(
                        f"/api/employees/{emp_id}",
                        headers=self._headers(),
                        name="/api/employees/{id}",
                    )
            elif resp.status_code == 401:
                resp.failure("Unauthorized — токен протух, намагаємось перелогінитись")
                self.on_start()
            elif resp.status_code == 409:
                resp.success()  # NFC UID дублюється — це не помилка тесту
            else:
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text[:200]}")

    @task(1)
    def get_audit_actions(self):
        """Список типів дій для фільтру."""
        self.client.get(
            "/api/audit/actions",
            headers=self._headers(),
            name="/api/audit/actions",
        )


# ─── Термінал (NFC-сканер) ────────────────────────────────────────────────────
class TerminalUser(HttpUser):
    """
    Імітує NFC-термінал: отримання challenge → secure-scan.
    Це найчастіший сценарій у реальній системі.
    """
    wait_time = between(2, 8)
    weight = 5  # терміналів набагато більше, ніж адмінів

    def _terminal_headers(self) -> dict:
        return {"X-API-Key": TERMINAL_API_KEY}

    @task(10)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(8)
    def secure_scan_flow(self):
        """
        Повний цикл безпечного сканування:
        1. Отримати challenge
        2. Надіслати secure-scan (підпис у тесті — фіктивний, перевіряємо лише статус і латентність)
        """
        # Крок 1: challenge
        with self.client.post(
            "/api/terminals/challenge",
            json={"terminal_id": TERMINAL_ID},
            headers=self._terminal_headers(),
            catch_response=True,
            name="/api/terminals/challenge",
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Challenge failed: {resp.status_code}")
                return
            challenge_b64 = resp.json().get("challenge_b64", "")

        # Крок 2: secure-scan (підпис не валідується в load-тесті — очікуємо 200 або 400/bad_signature)
        with self.client.post(
            "/api/terminals/secure-scan",
            json={
                "employee_uid": TEST_NFC_UID,
                "terminal_id": TERMINAL_ID,
                "direction": random.choice(DIRECTIONS),
                "challenge_b64": challenge_b64,
                "signature_b64": "dGVzdA==",  # фіктивний підпис
                "ts": None,
            },
            headers=self._terminal_headers(),
            catch_response=True,
            name="/api/terminals/secure-scan",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (400, 404):
                # bad_signature або employee not found — очікувано в тесті
                resp.success()
            else:
                resp.failure(f"Unexpected: {resp.status_code} — {resp.text[:200]}")

    @task(3)
    def simple_scan(self):
        """Простий скан без challenge (legacy /api/terminals/scan)."""
        with self.client.post(
            "/api/terminals/scan",
            json={
                "uid": TEST_NFC_UID,
                "terminal_id": TERMINAL_ID,
                "direction": random.choice(DIRECTIONS),
                "ts": None,
            },
            headers=self._terminal_headers(),
            catch_response=True,
            name="/api/terminals/scan",
        ) as resp:
            if resp.status_code in (200, 400, 404):
                resp.success()
            else:
                resp.failure(f"Scan error: {resp.status_code} — {resp.text[:200]}")

    @task(2)
    def nfc_event(self):
        """Відправка NFC-події через /api/events/nfc."""
        with self.client.post(
            "/api/events/nfc",
            json={
                "nfc_uid": TEST_NFC_UID,
                "direction": random.choice(DIRECTIONS),
                "ts": None,
            },
            headers=self._terminal_headers(),
            catch_response=True,
            name="/api/events/nfc",
        ) as resp:
            if resp.status_code in (200, 400, 404):
                resp.success()
            else:
                resp.failure(f"NFC event error: {resp.status_code}")


# ─── Hooks для звіту ──────────────────────────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n{'='*60}")
    print("  TimeTracker Load Test STARTED")
    print(f"  Host: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"\n{'='*60}")
    print("  TimeTracker Load Test FINISHED")
    stats = environment.stats.total
    print(f"  Total requests : {stats.num_requests}")
    print(f"  Failures       : {stats.num_failures}")
    fail_pct = (stats.num_failures / stats.num_requests * 100) if stats.num_requests else 0
    print(f"  Failure rate   : {fail_pct:.1f}%")
    print(f"  Avg response   : {stats.avg_response_time:.0f} ms")
    print(f"  95th pct       : {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"{'='*60}\n")
