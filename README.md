# TimeTracker

Система обліку робочого часу через NFC-термінали.  
FastAPI + MySQL + WebSocket + вбудована адмінка (SPA) + Docker.

---

## Можливості

- NFC-термінали — challenge-response автентифікація
- Live-дашборд — WebSocket оновлення в реальному часі
- Аналітика — звіти по часу, експорт PDF / XLSX
- Графік змін — планування + PDF-експорт
- Журнал аудиту — кожна дія адміна фіксується
- Ролі — Admin, Manager, HR, Employee

---

## Структура проекту

```
timetracker/
├── app/
│   ├── api/          # FastAPI routers
│   ├── core/         # config, logging, seed
│   ├── crud/         # операції з БД
│   ├── models/       # SQLAlchemy моделі
│   ├── schemas/      # Pydantic схеми
│   ├── services/     # бізнес-логіка
│   ├── static/       # SPA адмінка (index.html + JS)
│   ├── ws/           # WebSocket
│   └── main.py
├── alembic/          # міграції БД
├── docker/
│   ├── mysql/        # init.sql
│   └── nginx/        # nginx.conf + SSL
├── .env              # змінні оточення (є в репо)
├── .env.example      # шаблон з описом усіх змінних
├── docker-compose.yml         # production (з Nginx, порти 80/443)
├── docker-compose.dev.yml     # dev / VM (без Nginx, порт 8000)
├── Dockerfile
├── requirements.txt
├── deploy.sh         # перший запуск
├── update.sh         # оновлення без downtime
└── backup.sh         # бекап БД
```

---

## Запуск на локальній ВМ (Ubuntu + Docker)

### 1. Встановити Docker

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Клонувати проект

```bash
git clone https://github.com/ВАШ_АКАУНТ/timetracker.git
cd timetracker
```

### 3. Налаштувати .env

Файл `.env` вже є в репозиторії з базовими налаштуваннями.  
Перед запуском на продакшн-ВМ **обов'язково змініть паролі**:

```bash
nano .env
```

| Змінна | Опис |
|---|---|
| `DB_ROOT_PASSWORD` | пароль root MySQL |
| `DB_PASSWORD` | пароль користувача БД |
| `JWT_SECRET` | мін. 32 символи → `openssl rand -hex 64` |
| `ADMIN_PASSWORD` | пароль адміна |
| `APP_ENV` | `development` або `production` |
| `ALLOWED_ORIGINS` | `*` або `https://domain.com` |

### 4a. Запуск без Nginx (порт 8000) — найпростіше для ВМ

```bash
docker compose -f docker-compose.dev.yml up -d
```

- Адмінка: `http://IP_ВАШОЇ_ВМ:8000/admin/`
- Swagger:  `http://IP_ВАШОЇ_ВМ:8000/docs` (тільки `APP_ENV=development`)

### 4b. Запуск з Nginx (порти 80/443) — production

> Потребує SSL-сертифікатів. Якщо їх немає — використовуйте варіант 4a.

```bash
chmod +x deploy.sh
./deploy.sh
```

- Адмінка: `http://IP_ВАШОЇ_ВМ/admin/`

---

## SSL (необов'язково, тільки для варіанту 4b)

```bash
# Встановити certbot
sudo apt install -y certbot

# Зупинити Docker, отримати сертифікат
docker compose down
sudo certbot certonly --standalone -d yourdomain.com

# Скопіювати сертифікати
mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   docker/nginx/ssl/

# Запустити знову
./deploy.sh
```

Якщо SSL немає — у `docker/nginx/conf.d/timetracker.conf` приберіть блок `server { listen 443 ... }` і redirect, замінивши на прямий `proxy_pass` на порту 80.

---

## Мережа VirtualBox

Щоб ВМ була доступна з телефону/ПК у тій самій Wi-Fi мережі:

> **Налаштування → Мережа → Тип: Мережевий міст (Bridged Adapter)**

```bash
# Дізнатись IP ВМ
ip addr show | grep "inet " | grep -v 127

# Відкрити порти у firewall
sudo ufw allow 8000
sudo ufw allow 80
```

З телефону відкривати: `http://192.168.X.X:8000/admin/`

---

## Корисні команди

```bash
# Статус сервісів
docker compose ps

# Живі логи API
docker compose logs -f api

# Оновлення коду (git pull + rebuild)
./update.sh

# Бекап БД
./backup.sh

# Зупинити всі контейнери
docker compose down
```

---

## API

| Метод | Шлях | Опис |
|---|---|---|
| `GET` | `/health` | Стан сервісу |
| `GET` | `/admin/` | Адмін-панель |
| `GET` | `/docs` | Swagger UI (тільки `APP_ENV=development`) |
| `POST` | `/api/login` | Авторизація |
| `GET` | `/api/employees` | Список співробітників |
| `GET` | `/api/terminals` | Список терміналів |
| `GET` | `/api/stats/recent-scans` | Останні сканування |
| `GET` | `/api/export/worktime.xlsx` | Звіт по робочому часу |
| `GET` | `/api/schedule/pdf` | Експорт графіку PDF |
| `WS`  | `/ws/scans` | Live WebSocket |
