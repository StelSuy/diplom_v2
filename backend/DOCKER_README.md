# TimeTracker API — Запуск на виртуальной машине

## Структура файлов

```
проект/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .env                  ← создать из .env.example
├── docker/
│   └── mysql/
│       └── init.sql
├── app/
│   └── main.py
├── alembic/
└── requirements.txt
```

---

## 1. Подготовка виртуальной машины (Ubuntu/Debian)

```bash
# Обновить пакеты
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Установить Docker Compose (если нет)
sudo apt install docker-compose-plugin -y

# Проверить
docker --version
docker compose version
```

---

## 2. Клонировать проект и настроить .env

```bash
git clone <your-repo-url>
cd timetracker-api

# Создать .env из примера
cp .env.example .env

# Отредактировать — обязательно смени пароли!
nano .env
```

### Что менять в `.env`:
| Переменная | Что поставить |
|---|---|
| `MYSQL_ROOT_PASSWORD` | Любой сложный пароль |
| `DB_PASSWORD` | Любой сложный пароль |
| `SECRET_KEY` | Случайная строка: `openssl rand -hex 32` |
| `DB_HOST` | Оставить `db` (имя Docker-сервиса) |

---

## 3. Запустить

```bash
# Собрать образы и запустить все сервисы
docker compose up -d --build

# Посмотреть логи
docker compose logs -f

# Только логи API
docker compose logs -f api
```

После запуска:
- **API**: http://<IP_виртуальной_машины>:8000
- **Документация**: http://<IP_виртуальной_машины>:8000/docs

---

## 4. Управление

```bash
# Остановить
docker compose down

# Остановить и удалить данные БД (осторожно!)
docker compose down -v

# Перезапустить только API
docker compose restart api

# Войти в контейнер API
docker compose exec api bash

# Войти в MySQL
docker compose exec db mysql -u timetracker_user -p timetracker_db
```

---

## 5. Применить миграции вручную (если нужно)

```bash
docker compose exec api alembic upgrade head
```

---

## 6. Использование оригинального скрипта setup_database.ps1

Скрипт предназначен для **Windows без Docker**.  
На виртуальной машине с Docker он **не нужен** — база создаётся автоматически
через `docker-compose.yml` (переменные `MYSQL_*`).

Если всё же нужно запустить его на Windows против Docker MySQL:
- `DB_HOST` в `.env` укажи как IP виртуальной машины
- Порт 3306 должен быть открыт в firewall VM
