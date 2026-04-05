# TimeTracker — Система обліку робочого часу

Backend-сервер для автоматизованого обліку відвідуваності через NFC-термінали.  
**FastAPI · SQLAlchemy · MySQL · WebSocket · Docker · Gunicorn · Nginx**

---

## Можливості

- **NFC-термінали** — захищена авторизація через challenge-response (RSA + SHA-256)
- **Захист від replay-атак** — одноразові серверні challenge з TTL 30 сек
- **Live-дашборд** — WebSocket push-оновлення при кожному скані
- **Аналітика робочого часу** — підрахунок годин з урахуванням часового поясу (Europe/Warsaw)
- **Графіки змін** — планування + PDF-експорт
- **Ручні події** — адмін може додавати/видаляти відмітки
- **Журнал аудиту** — кожна адмін-дія зберігається в БД
- **Ролі доступу** — Admin / Manager / HR / Employee
- **Експорт** — XLSX-звіти по робочому часу, PDF-розклад
- **Rate limiting** — захист термінальних endpoint-ів (120 req/хв на IP)
- **Docker** — production-ready: MySQL + API + Nginx у трьох контейнерах

---

## Архітектура

```
app/
├── main.py                  — FastAPI app factory, lifespan, CORS, middleware
├── api/
│   ├── deps.py              — auth dependencies (JWT, terminal key, RBAC)
│   ├── router.py            — головний API router
│   └── routes/
│       ├── auth.py          — /api/login, /api/me
│       ├── employees.py     — CRUD співробітників
│       ├── terminals.py     — CRUD терміналів + /challenge + /secure-scan
│       ├── register.py      — /api/register/first-scan (реєстрація публічного ключа)
│       ├── events.py        — журнал сканувань
│       ├── manual_events.py — ручні відмітки
│       ├── schedules.py     — графіки змін
│       ├── stats.py         — статистика і аналітика
│       ├── export.py        — XLSX / PDF
│       ├── search.py        — пошук по співробітниках
│       ├── positions.py     — довідник посад
│       ├── users.py         — управління користувачами
│       └── audit_log.py     — журнал аудиту
├── core/
│   ├── config.py            — pydantic-settings (читає .env)
│   ├── logging.py           — налаштування логування
│   ├── security.py          — bcrypt, JWT
│   ├── seed.py              — початкові дані (admin + demo)
│   └── time.py              — часова зона Warsaw, конвертації UTC
├── crud/                    — операції з БД (employee, event, terminal, user, schedule)
├── db/
│   ├── base.py              — DeclarativeBase
│   ├── session.py           — engine + SessionLocal + get_db dep
│   └── init_db.py
├── models/                  — SQLAlchemy ORM (employee, event, terminal, user, schedule, position, audit_log)
├── schemas/                 — Pydantic v2 схеми (employee, event, terminal, schedule, stats, auth)
├── security/
│   ├── verify.py            — RSA підпис: verify_signature()
│   ├── challenge_store.py   — in-memory challenge store (TTL 30 сек)
│   ├── rate_limit.py        — in-memory rate limiter (120 req/хв)
│   └── audit.py             — запис аудит-логу
├── services/
│   └── worktime.py          — підрахунок робочих інтервалів, split по днях
├── ws/
│   ├── manager.py           — ConnectionManager (WebSocket)
│   ├── broadcast.py         — helpers для WS
│   └── routes.py            — /ws/scans endpoint
└── static/
    └── index.html           — SPA адмін-панель
```

---

## NFC Протокол (Challenge-Response)

```
Термінал                          Сервер
   │                                │
   │── POST /api/terminal/challenge ─▶│  { terminal_id }
   │◀─ { challenge_b64 } ────────────│  токен (32 байти, TTL 30 сек)
   │                                │
   │  [NFC: підписати challenge]    │
   │  [на телефоні → signature_b64] │
   │                                │
   │── POST /api/terminal/secure-scan▶│  { employee_uid, terminal_id,
   │                                │    direction, ts,
   │                                │    challenge_b64, signature_b64 }
   │◀─ { ok, employee_name, ... } ──│  сервер: consume_challenge()
   │                                │          + verify_signature()
   │                                │          + create event
   │                                │          + WS broadcast
```

Алгоритм підпису: **RSA-PKCS1v15 / SHA-256**.  
Публічний ключ зберігається в `employees.public_key_b64` (Base64 DER).

---

## База даних (таблиці)

| Таблиця | Опис |
|---|---|
| `employees` | Співробітники: ПІБ, nfc_uid, public_key_b64, посада |
| `events` | Журнал відміток: direction IN/OUT, ts (UTC), terminal_id |
| `terminals` | Термінали: name, api_key, is_active, last_seen_at |
| `users` | Адмін-користувачі: username, password_hash, role |
| `schedules` | Графіки: employee_id, day, start_hhmm, end_hhmm, code |
| `positions` | Довідник посад |
| `audit_log` | Журнал дій адмінів |

---

## API Endpoints

### Системні
| Метод | Шлях | Опис |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/` | Info |
| `GET` | `/admin/` | SPA адмін-панель |
| `GET` | `/docs` | Swagger (тільки `ENV=development`) |

### Авторизація
| Метод | Шлях | Опис |
|---|---|---|
| `POST` | `/api/login` | Отримати JWT токен |
| `GET` | `/api/me` | Поточний користувач |

### Термінальні (auth: `X-Terminal-Key`)
| Метод | Шлях | Опис |
|---|---|---|
| `POST` | `/api/terminal/challenge` | Отримати challenge |
| `POST` | `/api/terminal/secure-scan` | Захищений скан (підпис) |
| `POST` | `/api/terminal/scan` | Простий скан (без підпису) |
| `POST` | `/api/register/first-scan` | Зареєструвати публічний ключ |

### Адмін (auth: `Bearer <JWT>`)
| Метод | Шлях | Опис |
|---|---|---|
| `GET/POST` | `/api/employees` | Співробітники |
| `GET/POST` | `/api/terminals` | Термінали |
| `POST` | `/api/terminals/{id}/rotate_key` | Ротація API-ключа |
| `PATCH` | `/api/terminals/{id}/toggle_active` | Вмкн/вимкн термінал |
| `GET` | `/api/events` | Журнал подій |
| `POST` | `/api/manual-events` | Ручна відмітка |
| `GET` | `/api/stats/recent-scans` | Останні скани |
| `GET` | `/api/export/worktime.xlsx` | Excel-звіт |
| `GET` | `/api/schedule/pdf` | PDF-розклад |
| `GET` | `/api/audit-log` | Журнал аудиту |

### WebSocket
| Шлях | Опис |
|---|---|
| `WS /ws/scans` | Live push при кожному скані |

---

## Швидкий старт

### Варіант A — Docker (рекомендовано)

```bash
# 1. Клонувати
git clone https://github.com/YOUR_USER/timetracker.git
cd timetracker

# 2. Налаштувати
cp .env.example .env
nano .env   # змінити DB_PASSWORD, JWT_SECRET, ADMIN_PASSWORD

# 3. Запустити (без Nginx, порт 8000)
docker compose -f docker-compose.dev.yml up -d

# 4. Перевірити
curl http://localhost:8000/health
```

Адмінка: `http://localhost:8000/admin/`  
Swagger: `http://localhost:8000/docs` (тільки `APP_ENV=development`)

### Варіант B — Локально (SQLite, без Docker)

```bash
# 1. Налаштувати .env
cp .env.example .env
# Розкоментувати в .env: DATABASE_URL=sqlite:///./timetracker.db

# 2. Встановити залежності
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

pip install -r requirements.txt

# 3. Міграції
alembic upgrade head

# 4. Запустити
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Змінні оточення (.env)

| Змінна | Обов'язкова | За замовч. | Опис |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | SQLAlchemy URL (mysql або sqlite) |
| `JWT_SECRET` | ✅ | — | Мін. 32 символи (`openssl rand -hex 64`) |
| `ADMIN_PASSWORD` | ✅ | — | Пароль адміна (не `change_me` у production) |
| `APP_ENV` | | `production` | `development` вмикає Swagger, детальні логи |
| `ADMIN_USERNAME` | | `admin` | Логін адміна |
| `DB_ROOT_PASSWORD` | Docker | — | Root пароль MySQL |
| `DB_NAME` | Docker | `timetracker_db` | Ім'я БД |
| `DB_USER` | Docker | `timetracker_user` | Користувач БД |
| `DB_PASSWORD` | Docker | — | Пароль користувача БД |
| `ALLOWED_ORIGINS` | | `*` | CORS origins (через кому або `*`) |
| `TERMINAL_SCAN_COOLDOWN_SECONDS` | | `5` | Cooldown між сканами |
| `GUNICORN_WORKERS` | | `1` | Кількість воркерів (>1 потребує Redis) |
| `LOG_LEVEL` | | `info` | debug / info / warning / error |

> ⚠️ `GUNICORN_WORKERS > 1` не підтримується без Redis — challenge store і rate limiter in-memory і не шарять стан між процесами.

---

## Docker Compose

| Файл | Призначення |
|---|---|
| `docker-compose.yml` | Production: MySQL + API + Nginx (порти 80/443) |
| `docker-compose.dev.yml` | Dev/VM: MySQL + API (порт 8000, без Nginx) |

```bash
# Production з Nginx
./deploy.sh

# Dev без Nginx
docker compose -f docker-compose.dev.yml up -d

# Оновлення без downtime
./update.sh

# Бекап БД
./backup.sh
```

---

## Міграції (Alembic)

```bash
# Застосувати всі міграції
alembic upgrade head

# Створити нову міграцію
alembic revision --autogenerate -m "опис змін"

# Відкат на 1 кроку
alembic downgrade -1

# Поточна версія
alembic current
```

---

## Безпека

- **JWT** (HS256) для адмін-панелі
- **X-Terminal-Key** для NFC терміналів (Bearer-подібний токен)
- **RSA-PKCS1v15/SHA-256** — верифікація підпису (challenge-response)
- **One-time challenge** — захист від replay-атак (TTL 30 сек, consume при перевірці)
- **Rate limiting** — 120 req/хв на IP для термінальних endpoint-ів
- **bcrypt** — хешування паролів
- **Non-root Docker user** — контейнер запускається від `appuser`
- **Swagger вимкнено** у production (`APP_ENV=production`)

---

## Структура Docker

```
Dockerfile        — multi-stage: builder (gcc) → runtime (slim)
docker/
├── mysql/
│   └── init.sql  — початкові привілеї БД
└── nginx/
    ├── nginx.conf
    ├── conf.d/   — vhost конфіги
    └── ssl/      — SSL-сертифікати (не в git)
```

---

## Стек технологій

| Компонент | Технологія |
|---|---|
| Framework | FastAPI 0.115 |
| Server | Gunicorn + UvicornWorker |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | MySQL 8.0 / SQLite |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT) + bcrypt |
| Crypto | cryptography (RSA verify) |
| WebSocket | FastAPI native |
| Export | openpyxl (XLSX) + reportlab (PDF) |
| Proxy | Nginx 1.27 |
| Runtime | Python 3.12 |
| Container | Docker + Docker Compose |
