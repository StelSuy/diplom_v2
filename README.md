# TimeTracker

**Система обліку робочого часу через NFC-термінали.**

FastAPI backend + вбудована SPA-адмінка, WebSocket live-оновлення, MySQL/SQLite, Docker.

---

## Можливості

- NFC-термінали — захищений протокол challenge-response
- Live-дашборд — WebSocket оновлення сканувань у реальному часі
- Аналітика — денні/тижневі/місячні звіти, PDF та Excel-експорт
- Графік змін — планування + PDF-експорт з красивим оформленням
- Журнал аудиту — кожна дія адміна фіксується
- Ролі — Admin, Manager, HR, Employee

---

## Швидкий старт

### Варіант 1 — Docker (рекомендовано)

```bash
git clone https://github.com/StelSuy/diplom_v2.git timetracker
cd timetracker

# Налаштувати змінні оточення
cp .env.example .env
nano .env   # змінити DB_ROOT_PASSWORD, DB_PASSWORD, JWT_SECRET, ADMIN_PASSWORD

# Запустити
chmod +x deploy.sh
./deploy.sh
```

Адмінка: `http://localhost/admin/`
API docs: `http://localhost/docs`

---

### Варіант 2 — Docker (без Nginx, прямий порт 8000)

Підходить для локальної ВМ / тестування:

```bash
cp .env.example .env
nano .env

docker compose -f docker-compose.dev.yml up -d
```

Адмінка: `http://IP_вашої_машини:8000/admin/`

---

### Варіант 3 — Без Docker (SQLite, найпростіше)

```bash
git clone https://github.com/StelSuy/diplom_v2.git timetracker
cd timetracker

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
nano .env
```

У `.env` встановити:
```env
DATABASE_URL=sqlite:///./timetracker.db
JWT_SECRET=ваш_секретний_рядок_мінімум_32_символи
ADMIN_PASSWORD=ваш_пароль
APP_ENV=development
ALLOWED_ORIGINS=*
```

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Адмінка: `http://localhost:8000/admin/`

---

## Налаштування .env

| Змінна | Опис | Приклад |
|--------|------|---------|
| `DB_ROOT_PASSWORD` | Пароль root MySQL | `openssl rand -hex 16` |
| `DB_PASSWORD` | Пароль користувача БД | `openssl rand -hex 16` |
| `JWT_SECRET` | Секрет для JWT (**мін. 32 символи**) | `openssl rand -hex 64` |
| `ADMIN_PASSWORD` | Пароль адміна | мін. 8 символів |
| `ALLOWED_ORIGINS` | CORS-джерела | `*` або `https://domain.com` |
| `APP_ENV` | Середовище | `production` / `development` |
| `GUNICORN_WORKERS` | Кількість воркерів | `4` (2×CPU+1) |

---

## Розгортання на локальній ВМ

### 1. Дізнатись IP ВМ
```bash
ip addr show | grep "inet " | grep -v 127
# наприклад: 192.168.1.105
```

### 2. Налаштувати мережу ВМ
У VirtualBox: **Налаштування → Мережа → Тип підключення: Мережевий міст (Bridged)**

### 3. Відкрити порти в firewall (Ubuntu)
```bash
sudo ufw allow 8000
sudo ufw allow 80
```

### 4. Автостарт при завантаженні системи

```bash
sudo nano /etc/systemd/system/timetracker.service
```

```ini
[Unit]
Description=TimeTracker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/timetracker
ExecStart=docker compose up
ExecStop=docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable timetracker
sudo systemctl start timetracker
```

---

## Структура проекту

```
timetracker/
├── app/
│   ├── api/          # FastAPI routers
│   ├── core/         # config, security
│   ├── crud/         # DB operations
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # business logic
│   ├── static/       # SPA admin panel (index.html)
│   └── ws/           # WebSocket
├── alembic/          # DB migrations
├── docker/
│   ├── mysql/        # MySQL init script
│   └── nginx/        # Nginx config + SSL placeholder
├── .env.example      # ← копіювати в .env
├── docker-compose.yml         # production (з Nginx)
├── docker-compose.dev.yml     # development (без Nginx)
├── Dockerfile
├── requirements.txt
├── deploy.sh         # перший запуск
├── update.sh         # оновлення без downtime
└── backup.sh         # бекап БД (для cron)
```

---

## API

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/health` | Стан сервісу |
| `GET` | `/admin/` | Адмін-панель |
| `GET` | `/docs` | Swagger UI (тільки dev) |
| `POST` | `/api/login` | Авторизація |
| `GET` | `/api/stats/recent-scans` | Останні сканування |
| `GET` | `/api/schedule/pdf` | Експорт графіку в PDF |
| `GET` | `/api/export/worktime.xlsx` | Звіт по робочому часу |
| `WS` | `/ws/scans` | Live WebSocket |

---

## Оновлення

```bash
./update.sh
```

## Бекап БД

```bash
./backup.sh
# або автоматично через cron:
# 0 2 * * * /home/ubuntu/timetracker/backup.sh
```
