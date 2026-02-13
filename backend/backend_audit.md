# 🔍 Аудит Backend — TimeTracker API

---

## 🐛 ЧАСТИНА 1: ЗНАЙДЕНІ БАГИ

### БАГ №1 — Подвійна авторизація в admin-ендпоінтах (КРИТИЧНО)
**Файли:** `employees.py`, `manual_events.py`, `terminals.py`

Роутери оголошені з `dependencies=[Depends(require_admin)]` на рівні роутера, **і при цьому окремі ендпоінти всередині додатково отримують `current_user: User = Depends(get_current_user)`**.

`require_admin` перевіряє JWT і роль, але **не повертає об'єкт User з БД** — він повертає `dict` (payload).  
`get_current_user` — робить окремий запит до БД і повертає `User`.

**Проблема:**  
```python
# employees.py
router = APIRouter(dependencies=[Depends(require_admin)])  # ← перевіряє JWT + роль

@router.post("/")
def create_employee(
    current_user: User = Depends(get_current_user),  # ← робить ЩЕ ОДИН запит до БД
):
```
Це призводить до **двох декодувань JWT** та **двох запитів до БД** на кожен запит. Якщо `require_admin` успішно пройдений, `get_current_user` все одно може повернути помилку якщо користувач видалений з БД між двома перевірками.

**Виправлення:** Змінити `require_admin` щоб він повертав `User`:
```python
def require_admin(db: Session = Depends(get_db), credentials=...) -> User:
    payload = _decode_jwt(credentials)
    if payload.get("role") != "admin":
        raise HTTPException(403, "Insufficient privileges")
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

---

### БАГ №2 — `datetime.utcnow()` застарілий і небезпечний
**Файл:** `manual_events.py`, рядок ~98

```python
created_at=datetime.utcnow(),  # ← DEPRECATED в Python 3.12+
```

`datetime.utcnow()` повертає **naive datetime** без timezone info. У Python 3.12+ це викликає DeprecationWarning, у майбутніх версіях — помилку.

**Виправлення:**
```python
created_at=datetime.now(timezone.utc),
```

---

### БАГ №3 — Глобальний стан пароля адміна (`_admin_password_hash`)
**Файл:** `auth.py`

```python
_admin_password_hash: str | None = None

def _get_admin_hash() -> str:
    global _admin_password_hash
    ...
```

При **multi-worker** деплойменті (gunicorn + кілька воркерів) кожен воркер матиме свій екземпляр `_admin_password_hash`. Це не баг безпеки, але означає що хешування виконується **знову в кожному воркері** при першому логіні, що безглуздо як оптимізація.

Більш серйозно: якщо `settings.admin_password` зміниться (hot reload), старий хеш залишиться в пам'яті.

**Виправлення:** Хешувати при старті застосунку в `on_startup`, або просто **не кешувати** — bcrypt.checkpw достатньо швидкий:
```python
@router.post("/login")
def login(payload: LoginRequest):
    if payload.username != settings.admin_username:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(payload.password, hash_password(settings.admin_password)):
        raise HTTPException(401, "Invalid credentials")
    ...
```
Або кешувати в `settings` як computed field.

---

### БАГ №4 — Rate limiter не захищає `/login`
**Файли:** `rate_limit.py`, `auth.py`

`check_rate_limit` застосований лише до `router_public` (термінальні ендпоінти). Ендпоінт `/api/auth/login` **не має жодного rate limiting**, що відкриває його для brute-force атак на пароль адміна.

**Виправлення:** Додати `Depends(check_rate_limit)` до роутера авторизації:
```python
@router.post("/login", dependencies=[Depends(check_rate_limit)])
def login(payload: LoginRequest):
    ...
```

---

### БАГ №5 — Небезпечне логування API-ключа терміналу
**Файл:** `deps.py`

```python
logger.warning(f"Invalid terminal key: {x_terminal_key[:8]}...")
```

Навіть перші 8 символів API-ключа не варто логувати — це полегшує атаки. API-ключ — секрет.

**Виправлення:**
```python
logger.warning("Invalid terminal key attempt")
```

---

### БАГ №6 — Відсутня валідація діапазону дат у `stats.py`
**Файл:** `stats.py`

```python
@router.get("/employee/{employee_id}/daily")
def employee_daily_stats(
    from_date: date = Query(...),
    to_date: date = Query(...),
):
```

Немає перевірки що `from_date <= to_date`. Запит з `from_date=2026-12-31&to_date=2026-01-01` викличе нескінченний цикл у `iter_local_days` (або просто поверне порожній результат, залежно від реалізації — але це некоректна поведінка).

**Виправлення:**
```python
if from_date > to_date:
    raise HTTPException(400, "from_date must be <= to_date")
if (to_date - from_date).days > 365:
    raise HTTPException(400, "Date range too large (max 365 days)")
```

---

### БАГ №7 — `create_event` і `create_event_from_terminal_scan` дублюють логіку
**Файл:** `event.py` (crud)

Є дві окремі функції: `create_event` (викликається з `events.py` route) та `create_event_from_terminal_scan` (викликається з `terminals.py`). Обидві створюють `Event` об'єкт, але друга ще й визначає напрямок автоматично. Це нормально архітектурно, але `create_event` **не перевіряє cooldown**, а `create_event_from_terminal_scan` — перевіряє. Якщо хтось звернеться до `POST /api/events/nfc` напряму, cooldown буде обходитись.

---

### БАГ №8 — Bare `except:` у PDF-генерації
**Файл:** `schedules.py`

```python
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    font_name = 'DejaVuSans'
except:          # ← ловить ВСЕ, включаючи KeyboardInterrupt, SystemExit
    try:
        ...
    except:      # ← і тут теж
        ...
```

**Виправлення:**
```python
except Exception:
    ...
```

---

### БАГ №9 — `update_employee` пропускає `None` значення без можливості скинути поле
**Файл:** `employee.py` (crud)

```python
def update_employee(db, emp, data):
    for k, v in data.items():
        if v is not None:  # ← не можна скинути поле в None через PATCH
            setattr(emp, k, v)
```

Якщо адмін хоче прибрати `comment` (встановити в `null`), запит `{"comment": null}` буде ігнорований.

**Виправлення:** Використовувати `model_dump(exclude_unset=True)` (вже є в route), але в crud прибрати фільтр `None`:
```python
for k, v in data.items():
    setattr(emp, k, v)  # дозволяємо None
```

---

### БАГ №10 — WebSocket `broadcast` не є thread-safe при concurrent scans
**Файл:** `ws/manager.py`

`self._connections` — звичайний список Python. При одночасних скануваннях з кількох терміналів можлива race condition при модифікації списку (`dead` cleanup). У production краще використовувати `asyncio.Lock`.

---

## 🚀 ЧАСТИНА 2: РЕКОМЕНДАЦІЇ ПО ПОКРАЩЕННЮ

### ПОКРАЩЕННЯ №1 — Pagination для всіх list-ендпоінтів

`GET /employees/` повертає **всіх** співробітників без ліміту. При великій кількості — проблема.

```python
@router.get("/", response_model=list[EmployeeOut])
def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return db.query(Employee).order_by(Employee.id).offset(skip).limit(limit).all()
```

---

### ПОКРАЩЕННЯ №2 — Індекс на `events.ts` + compound index

У `Event` є `index=True` на `ts`, але для статистичних запитів типу "всі події за певну дату для певного співробітника" потрібен **compound index**:

```python
# У міграції alembic:
op.create_index('ix_events_employee_ts', 'events', ['employee_id', 'ts'])
```

---

### ПОКРАЩЕННЯ №3 — Refresh token механізм

Зараз токени живуть 60 хвилин і після закінчення — logout. Варто додати refresh token:
- Short-lived access token (15 хв)  
- Long-lived refresh token (7 днів) у HTTP-only cookie

---

### ПОКРАЩЕННЯ №4 — Валідація NFC UID формату

У `employee.py` і `event.py` UID нормалізується через `.strip().upper()`, але немає валідації формату. Можна передати порожній рядок або дуже довгий рядок.

```python
# schemas/employee.py
from pydantic import validator

@validator('nfc_uid')
def validate_nfc_uid(cls, v):
    v = v.strip().upper()
    if not v:
        raise ValueError("NFC UID cannot be empty")
    if len(v) > 64:
        raise ValueError("NFC UID too long")
    return v
```

---

### ПОКРАЩЕННЯ №5 — Health check з перевіркою БД

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status, "version": "1.0.0"}
```

---

### ПОКРАЩЕННЯ №6 — Винести hardcoded "Europe/Warsaw" в config

У `stats.py`, `manual_events.py`, `worktime.py` часовий пояс `Europe/Warsaw` захардкоджений. Варто:

```python
# config.py
timezone: str = "Europe/Warsaw"
```

---

### ПОКРАЩЕННЯ №7 — Structured logging замість f-strings

Замінити:
```python
logger.info(f"User authenticated: {username}")
```
На:
```python
logger.info("User authenticated", extra={"username": username})
```
Це дозволяє парсити логи в ELK/Loki.

---

## 🧪 ЧАСТИНА 3: ФЕЙКОВА БД ДЛЯ ТЕСТУВАННЯ

### Підхід: SQLite в пам'яті + pytest fixtures

Найкращий підхід для FastAPI + SQLAlchemy — використовувати **SQLite in-memory** базу та **dependency override**.

---

### Крок 1: Встановити залежності для тестів

```bash
pip install pytest pytest-asyncio httpx
```

Додати до `requirements.txt`:
```
# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
```

---

### Крок 2: Створити `tests/conftest.py`

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token

# -------------------------------------------------------
# ФЕЙКОВА БД — SQLite in-memory
# -------------------------------------------------------
TEST_DB_URL = "sqlite://"  # чиста пам'ять, без файлу

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # одне з'єднання для всіх тестів
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Створює всі таблиці один раз перед тестами."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Повертає сесію фейкової БД, що відкочується після кожного тесту."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()  # ← відкочує всі зміни після тесту!
    connection.close()


@pytest.fixture
def client(db):
    """TestClient з підміненою залежністю get_db."""
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    """JWT токен адміна для тестів."""
    return create_access_token(subject="admin", extra={"role": "admin"})


@pytest.fixture
def admin_headers(admin_token):
    """Заголовки з токеном адміна."""
    return {"Authorization": f"Bearer {admin_token}"}


# -------------------------------------------------------
# ФАБРИКИ ТЕСТОВИХ ДАНИХ
# -------------------------------------------------------
@pytest.fixture
def test_terminal(db):
    from app.models.terminal import Terminal
    import secrets
    terminal = Terminal(
        id=1,
        name="Test Terminal",
        api_key=secrets.token_urlsafe(32),
    )
    db.add(terminal)
    db.commit()
    db.refresh(terminal)
    return terminal


@pytest.fixture
def test_employee(db):
    from app.models.employee import Employee
    employee = Employee(
        full_name="Іван Тестовий",
        nfc_uid="TEST-UID-0001",
        position="Тестувальник",
        is_active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture
def terminal_headers(test_terminal):
    """Заголовки з API-ключем терміналу."""
    return {"X-Terminal-Key": test_terminal.api_key}
```

---

### Крок 3: Приклади тестів

```python
# tests/test_auth.py
def test_login_success(client):
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "your_test_password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrong"
    })
    assert response.status_code == 401


# tests/test_employees.py
def test_create_employee(client, admin_headers):
    response = client.post("/api/employees/", json={
        "full_name": "Петро Іванов",
        "nfc_uid": "ABCD1234",
    }, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Петро Іванов"
    assert data["nfc_uid"] == "ABCD1234"


def test_list_employees_unauthorized(client):
    response = client.get("/api/employees/")
    assert response.status_code == 401


# tests/test_events.py
def test_nfc_scan(client, test_employee, test_terminal, terminal_headers):
    from datetime import datetime, timezone
    response = client.post("/api/events/nfc", json={
        "nfc_uid": "TEST-UID-0001",
        "direction": "IN",
        "ts": datetime.now(timezone.utc).isoformat(),
    }, headers=terminal_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_nfc_scan_unknown_employee(client, test_terminal, terminal_headers):
    from datetime import datetime, timezone
    response = client.post("/api/events/nfc", json={
        "nfc_uid": "UNKNOWN-UID",
        "direction": "IN",
        "ts": datetime.now(timezone.utc).isoformat(),
    }, headers=terminal_headers)
    assert response.status_code == 404


# tests/test_stats.py
def test_stats_no_events(client, test_employee, admin_headers):
    response = client.get(f"/api/stats/employee/{test_employee.id}", 
                          headers=admin_headers)
    assert response.status_code == 404  # "No events for employee"
```

---

### Крок 4: `pytest.ini` або `pyproject.toml`

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

---

### Крок 5: Запуск тестів

```bash
# Запустити всі тести
pytest

# З виводом
pytest -v

# Конкретний файл
pytest tests/test_employees.py -v

# Зі звітом покриття
pytest --cov=app --cov-report=html
```

---

## 📊 ПІДСУМОК

| Категорія | Кількість |
|-----------|-----------|
| 🔴 Критичні баги | 2 (подвійна авторизація, відсутній rate limit на login) |
| 🟠 Важливі баги | 4 (datetime.utcnow, глобальний стан, bare except, None update) |
| 🟡 Мінорні баги | 4 (логування ключа, валідація дат, cooldown bypass, race condition WS) |
| 🔵 Покращення | 7 (pagination, indexes, refresh token, тощо) |

Загалом проект **добре структурований** — чіткий поділ на шари (models/crud/schemas/routes), є аудит-логи, rate limiting, challenge-response для безпечного сканування. Після виправлення зазначених проблем буде production-ready.
