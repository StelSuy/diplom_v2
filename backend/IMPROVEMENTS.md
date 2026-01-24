# Улучшения Backend - ДИПЛОМ

## ✅ Исправлено

### 1. Добавлен эндпоинт `POST /api/schedule` для массового сохранения
**Проблема:** Фронтенд отправлял `POST /api/schedule`, но был только `POST /api/schedule/cell`

**Решение:**
- Добавлена схема `ScheduleBatchUpsert` и `ScheduleBatchResponse`
- Добавлен роут `POST /api/schedule` для batch операций
- Теперь можно сохранять несколько ячеек за один запрос

**Пример запроса:**
```json
POST /api/schedule
{
  "cells": [
    {"employee_id": 1, "day": "2026-01-02", "code": "8-17"},
    {"employee_id": 2, "day": "2026-01-02", "start_hhmm": "09:00", "end_hhmm": "18:00"}
  ]
}
```

**Ответ:**
```json
{
  "success": 2,
  "failed": 0,
  "errors": []
}
```

---

## 🔴 КРИТИЧЕСКИЕ проблемы (требуют исправления)

### 1. Дублирование функции `get_db()`
**Файлы:** 
- `app/api/deps.py` (строки внизу файла)
- `app/db/session.py`

**Проблема:** Функция определена дважды, это может вызвать конфликты импортов.

**Решение:** Удалить из `app/api/deps.py`:
```python
# УДАЛИТЬ ЭТИ СТРОКИ:
from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Оставить только в `app/db/session.py` и импортировать оттуда.

---

### 2. Отсутствует зависимость `cryptography`
**Файл:** `requirements.txt`

**Проблема:** В `app/security/verify.py` используется библиотека `cryptography`, но она не указана в зависимостях.

**Решение:** Добавить в `requirements.txt`:
```txt
cryptography==41.0.7
```

---

### 3. Некорректный тип `terminal_id` в модели Event
**Файл:** `app/models/event.py`

**Проблема:** 
- `terminal_id` объявлен как `ForeignKey("terminals.id")` → ожидается Integer
- Но в CRUD используется `str(terminal_id)`
- Это несоответствие типов

**Решение:** Определиться с типом:

**Вариант A** (если Terminal.id это Integer):
```python
# app/models/event.py
terminal_id: Mapped[int] = mapped_column(ForeignKey("terminals.id"), index=True)

# app/crud/event.py - убрать str()
ev = Event(
    employee_id=employee_id,
    terminal_id=terminal_id,  # НЕ str(terminal_id)
    direction=direction,
    ts=ts_utc,
)
```

**Вариант B** (если Terminal.id это String):
```python
# app/models/terminal.py
id: Mapped[str] = mapped_column(String(64), primary_key=True)

# app/models/event.py
terminal_id: Mapped[str] = mapped_column(String(64), ForeignKey("terminals.id"), index=True)
```

---

### 4. README.md с кракозябрами
**Файл:** `README.md`

**Проблема:** Кириллица отображается как мусор (неправильная кодировка)

**Решение:** Пересохранить файл в UTF-8 с правильным текстом:
```markdown
# Backend (FastAPI)

Команды запуска:
- Windows: run_dev.bat
- Linux/Mac: ./run_dev.sh

ENV:
- Скопируй .env.example → .env и настрой.
```

---

## ⚠️ ВАЖНЫЕ улучшения (настоятельно рекомендуется)

### 5. Небезопасное хранение секретов
**Файл:** `app/core/config.py`

**Проблема:**
```python
jwt_secret: str = "change_me"  # ❌ Это дефолт для production!
admin_username: str = "admin"
admin_password: str = "admin123"
```

**Решение:**
```python
# .env
JWT_SECRET=<случайная_строка_64_символа>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<сложный_пароль>

# app/core/config.py
from secrets import token_urlsafe

class Settings(BaseSettings):
    jwt_secret: str = Field(
        default_factory=lambda: token_urlsafe(32),
        description="Must be set in production!"
    )
    
    @validator('jwt_secret')
    def check_jwt_secret(cls, v):
        if v == "change_me":
            raise ValueError("JWT_SECRET must be changed in production!")
        return v
```

---

### 6. Отсутствие CORS
**Файл:** `app/main.py`

**Проблема:** Фронтенд не сможет делать запросы с другого домена/порта.

**Решение:**
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.app_name)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # фронтенд URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 7. Отсутствие миграций БД (Alembic)
**Проблема:** Изменения схемы БД нужно применять вручную через `init_db.py`

**Решение:** Настроить Alembic:
```bash
pip install alembic
alembic init alembic
```

```python
# alembic/env.py
from app.db.base import Base
from app.models import *  # импортируем все модели

target_metadata = Base.metadata
```

```bash
# Создать миграцию
alembic revision --autogenerate -m "initial"

# Применить миграцию
alembic upgrade head
```

---

### 8. Отсутствие Structured Logging
**Файл:** `app/main.py`

**Проблема:** Используются print() вместо logger

**Решение:**
```python
# app/core/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5)
        ]
    )

# app/main.py
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    logger.info("Application starting...")
```

---

### 9. Отсутствие пагинации
**Файл:** `app/api/routes/employees.py`

**Проблема:** `GET /employees/` вернёт ВСЕ записи (проблема при 10000+ сотрудников)

**Решение:**
```python
from fastapi import Query

@router.get("/", response_model=list[EmployeeOut])
def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees
```

---

### 10. Health check не проверяет БД
**Файл:** `app/main.py`

**Проблема:** `/health` возвращает статус, но не проверяет соединение с БД

**Решение:**
```python
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        # Простой запрос для проверки БД
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}
```

---

## 💡 Архитектурные улучшения

### 11. Централизованная обработка ошибок
**Файл:** `app/core/exceptions.py` (создать новый)

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(IntegrityError)
async def db_integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violation"},
    )
```

---

### 12. Rate Limiting для терминалов
**Файл:** `app/api/routes/events.py`

**Проблема:** Терминал может спамить события

**Решение:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/nfc")
@limiter.limit("10/minute")  # макс 10 запросов в минуту
def create_nfc_event(...):
    ...
```

---

### 13. API Versioning
**Файл:** `app/main.py`

**Проблема:** Нет версионирования API

**Решение:**
```python
# Текущее
app.include_router(api_router, prefix="/api")

# Лучше
app.include_router(api_router, prefix="/api/v1")
```

---

### 14. Добавить Docker
**Файл:** `Dockerfile` (создать)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Файл:** `docker-compose.yml` (создать)

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db:3306/timetracker
    depends_on:
      - db
  
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: timetracker
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

---

### 15. Экспорт данных в Excel/CSV
**Файл:** `app/api/routes/stats.py`

```python
from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/employee/{employee_id}/export")
def export_employee_stats(employee_id: int, db: Session = Depends(get_db)):
    events = event_crud.list_events_for_employee(db, employee_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Direction", "Timestamp", "Terminal"])
    
    for ev in events:
        writer.writerow([ev.id, ev.direction, ev.ts.isoformat(), ev.terminal_id])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=employee_{employee_id}_events.csv"}
    )
```

---

## 📦 Обновлённый requirements.txt

```txt
# Web Framework
fastapi==0.115.0
uvicorn[standard]==0.30.6

# Data Validation
pydantic==2.8.2
pydantic-settings==2.4.0

# Database
SQLAlchemy==2.0.32
alembic==1.13.1  # NEW: для миграций
pymysql==1.1.0   # NEW: если используется MySQL

# Security
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
cryptography==41.0.7  # NEW: для verify.py

# Utilities
python-dotenv==1.0.1

# PDF Generation (уже используется)
reportlab==4.0.7

# Rate Limiting (опционально)
slowapi==0.1.9

# CORS (встроено в FastAPI, но для явности)
# python-multipart  # если нужна загрузка файлов
```

---

## 🧪 Тесты (создать)

**Файл:** `tests/test_schedule.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_batch_upsert_schedule():
    # Получить токен
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Сохранить расписание
    response = client.post(
        "/api/schedule",
        json={
            "cells": [
                {"employee_id": 1, "day": "2026-01-02", "code": "8-17"}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == 1
    assert data["failed"] == 0
```

---

## 📝 Следующие шаги

1. ✅ Исправить критические ошибки (1-4)
2. ⚠️ Добавить CORS и логирование (5-8)
3. 💡 Внедрить архитектурные улучшения (9-15)
4. 🧪 Написать тесты
5. 🐳 Настроить Docker для удобного деплоя
6. 📚 Обновить документацию

---

## 🎯 Приоритеты для диплома

### Высокий приоритет (сделать обязательно):
- ✅ POST /api/schedule (уже сделано)
- Исправить дублирование get_db()
- Добавить cryptography в requirements
- Настроить CORS
- Добавить proper logging

### Средний приоритет (улучшит впечатление):
- Настроить Alembic
- Добавить пагинацию
- Health check с проверкой БД
- Исправить terminal_id тип

### Низкий приоритет (для production, но не критично для диплома):
- Rate limiting
- Docker
- Расширенные тесты
- API versioning
