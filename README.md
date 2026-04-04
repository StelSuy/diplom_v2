# TimeTracker

**Employee attendance tracking system via NFC terminals.**

A production-ready FastAPI backend with a built-in admin panel, WebSocket live updates, MySQL database, and Docker deployment.

---

## Features

- **NFC terminal support** — secure scan flow with challenge-response signature verification
- **Real-time dashboard** — WebSocket live feed of employee scans
- **Admin panel** — full SPA (no external build tools required)
- **Worktime analytics** — daily/weekly/monthly reports, PDF & Excel export
- **Schedule management** — plan vs. actual with PDF export
- **Audit log** — every admin action is recorded
- **Role-based access** — Admin, Manager, HR, Employee roles
- **Docker-ready** — multi-stage Dockerfile, Nginx reverse proxy, Gunicorn workers

---

## Quick Start (Docker)

### 1. Clone & configure

```bash
git clone <your-repo-url> timetracker
cd timetracker

cp .env.example .env
nano .env           # fill in DB_ROOT_PASSWORD, DB_PASSWORD, JWT_SECRET, ADMIN_PASSWORD
```

### 2. Deploy

```bash
chmod +x deploy.sh update.sh backup.sh
./deploy.sh
```

### 3. Open admin panel

```
http://<your-server-ip>/admin
```

Default login: `admin` / your `ADMIN_PASSWORD` from `.env`

---

## Development

```bash
# Copy and edit env for local dev
cp .env.example .env

# Start with hot-reload
docker compose -f docker-compose.dev.yml up

# Or run without Docker (requires MySQL running locally)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs (dev only): http://localhost:8000/docs

---

## Project Structure

```
timetracker/
├── app/
│   ├── api/
│   │   ├── deps.py              # Auth dependencies (JWT, terminal key)
│   │   ├── router.py            # Route aggregator
│   │   └── routes/              # Feature routes
│   │       ├── auth.py          # Login
│   │       ├── employees.py     # Employee CRUD
│   │       ├── terminals.py     # Terminal management + NFC scan
│   │       ├── events.py        # NFC event recording
│   │       ├── stats.py         # Worktime statistics
│   │       ├── schedules.py     # Schedule management
│   │       ├── manual_events.py # Manual attendance correction
│   │       ├── export.py        # Excel / PDF export
│   │       ├── audit_log.py     # Audit trail
│   │       ├── users.py         # User management
│   │       └── positions.py     # Job positions
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── security.py          # JWT, password hashing
│   │   ├── logging.py           # Logging setup
│   │   ├── seed.py              # Initial data seeding
│   │   └── time.py              # Timezone utilities
│   ├── crud/                    # Database operations
│   ├── db/                      # SQLAlchemy engine + session
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── security/                # NFC signature verification, rate limiting
│   ├── services/                # Business logic (worktime calculation)
│   ├── static/                  # Admin panel SPA (index.html)
│   ├── ws/                      # WebSocket live scan feed
│   └── main.py                  # App factory + lifespan
├── alembic/                     # Database migrations
├── docker/
│   ├── mysql/init.sql           # MySQL initialization
│   └── nginx/                   # Nginx config + SSL placeholder
├── .env.example                 # Environment template
├── Dockerfile                   # Multi-stage production image
├── docker-compose.yml           # Production stack
├── docker-compose.dev.yml       # Development stack
├── deploy.sh                    # First-time deployment script
├── update.sh                    # Zero-downtime update script
└── backup.sh                    # Database backup script
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Full MySQL connection URL |
| `JWT_SECRET` | ✅ | — | Min 32 chars, generate with `openssl rand -hex 64` |
| `ADMIN_PASSWORD` | ✅ | — | Admin account password (changed from default) |
| `DB_ROOT_PASSWORD` | ✅ | — | MySQL root password |
| `DB_PASSWORD` | ✅ | — | MySQL app user password |
| `APP_ENV` | | `production` | `development` or `production` |
| `ALLOWED_ORIGINS` | | `*` | Comma-separated CORS origins |
| `GUNICORN_WORKERS` | | `2` | Number of worker processes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `60` | JWT token TTL |
| `LOG_LEVEL` | | `info` | Logging verbosity |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/login` | Authenticate, get JWT token |
| `GET` | `/api/employees/` | List employees |
| `POST` | `/api/employees/` | Create employee |
| `GET` | `/api/terminals/` | List NFC terminals |
| `POST` | `/api/terminal/scan` | Record NFC scan |
| `POST` | `/api/terminal/secure-scan` | Secure scan (challenge-response) |
| `GET` | `/api/stats/recent-scans` | Today's scans dashboard |
| `GET` | `/api/stats/employee/{id}/daily` | Daily worktime report |
| `GET` | `/api/export/worktime.xlsx` | Export worktime to Excel |
| `GET` | `/api/export/worktime.pdf` | Export worktime to PDF |
| `GET` | `/api/audit/log` | Audit log |
| `WS` | `/ws/scans` | Live scan feed (WebSocket) |
| `GET` | `/health` | Health check |

Full interactive docs (dev mode): `/docs`

---

## Operations

### Update deployment

```bash
./update.sh
```

### Backup database

```bash
./backup.sh

# Backups are stored in ./backups/
# Rotated automatically (keeps last 7 days)
```

### View logs

```bash
docker compose logs -f api      # API logs
docker compose logs -f nginx    # Nginx logs
docker compose logs -f db       # MySQL logs
```

### Run migrations manually

```bash
docker compose exec api alembic upgrade head
```

### SSL with Certbot

```bash
# Install certbot
apt install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Copy to nginx ssl dir
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/

# Update server_name in docker/nginx/conf.d/timetracker.conf
# Restart nginx
docker compose restart nginx
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| Framework | FastAPI 0.115 |
| Server | Gunicorn + Uvicorn workers |
| Database | MySQL 8.0 + SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| WebSocket | FastAPI native |
| Reverse proxy | Nginx 1.27 |
| Container | Docker + Docker Compose |
| Export | ReportLab (PDF) + OpenPyXL (Excel) |

---

## License

MIT
