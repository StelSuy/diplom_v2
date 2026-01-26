# 🕐 TimeTracker API - Система обліку робочого часу

Сучасний backend для відстеження робочого часу співробітників за допомогою NFC-терміналів.

## 📋 Зміст

- [Про проєкт](#про-проєкт)
- [Технології](#технології)
- [Швидкий старт](#швидкий-старт)
- [Налаштування](#налаштування)
- [Розробка](#розробка)
- [API документація](#api-документація)
- [Міграції БД](#міграції-бд)
- [Deployment](#deployment)
- [Підтримка](#підтримка)

---

## 🎯 Про проєкт

TimeTracker - це REST API для автоматизованого обліку робочого часу:

- ✅ Реєстрація входу/виходу через NFC-термінали
- ✅ Ручне додавання подій адміністратором
- ✅ Автоматичний підрахунок відпрацьованих годин
- ✅ Підтримка графіків роботи
- ✅ Детальна статистика по співробітниках
- ✅ Безпечна автентифікація (JWT + Challenge-Response)
- ✅ Підтримка часових зон (Europe/Warsaw)

---

## 🛠 Технології

- **Framework:** FastAPI 0.115.0
- **ORM:** SQLAlchemy 2.0.32
- **Database:** MySQL/MariaDB (або PostgreSQL/SQLite)
- **Міграції:** Alembic 1.13.1
- **Автентифікація:** JWT (python-jose)
- **Валідація:** Pydantic 2.8.2
- **Password hashing:** Bcrypt (passlib)

---

## 🚀 Швидкий старт

### 1. Передумови

- Python 3.12+
- MySQL/MariaDB (або PostgreSQL)
- pip або poetry

### 2. Клонування та встановлення

```bash
# Клонування репозиторію
git clone <repository-url>
cd backend

# Створення віртуального середовища
python -m venv .venv

# Активація (Windows)
.venv\Scripts\activate

# Активація (Linux/Mac)
source .venv/bin/activate

# Встановлення залежностей
pip install -r requirements.txt
```

### 3. Налаштування бази даних

```bash
# Створіть базу даних MySQL
mysql -u root -p
CREATE DATABASE timetracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'timetracker'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON timetracker.* TO 'timetracker'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Налаштування .env

```bash
# Скопіюйте приклад
cp .env.example .env

# Відредагуйте .env файл (обов'язково!)
# Змініть DATABASE_URL та JWT_SECRET
```

### 5. Міграції

```bash
# Застосувати всі міграції
alembic upgrade head
```

### 6. Запуск сервера

```bash
# Режим розробки (з авто-перезавантаженням)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Або через скрипт
.\run_dev.bat  # Windows
./run_dev.sh   # Linux/Mac
```

Сервер буде доступний на: http://localhost:8000

- **API документація:** http://localhost:8000/docs
- **Альтернативна документація:** http://localhost:8000/redoc
- **Admin панель:** http://localhost:8000/admin

---

## ⚙️ Налаштування

### Файл .env

Основні параметри конфігурації:

```env
# Додаток
APP_NAME=TimeTracker API
ENV=dev
DEBUG=true

# База даних
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/timetracker

# Безпека
JWT_SECRET=your-super-secret-key-min-32-characters
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Адміністратор (тільки для seed)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Термінали
TERMINAL_SCAN_COOLDOWN_SECONDS=5

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# База даних (додаткові параметри)
SQL_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
```

### Важливі налаштування для production

1. **JWT_SECRET** - згенерувати випадковий ключ:
   ```bash
   openssl rand -hex 32
   ```

2. **DEBUG** - встановити `false`

3. **CORS_ORIGINS** - вказати реальні домени

4. **DATABASE_URL** - використовувати production credentials

---

## 💻 Розробка

### Структура проєкту

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── routes/       # Маршрути
│   │   ├── deps.py       # Залежності (auth)
│   │   └── router.py     # Головний роутер
│   ├── core/             # Ядро додатку
│   │   ├── config.py     # Налаштування
│   │   ├── security.py   # JWT, bcrypt
│   │   └── time.py       # Робота з часовими зонами
│   ├── crud/             # CRUD операції
│   ├── db/               # База даних
│   │   ├── base.py       # SQLAlchemy Base
│   │   └── session.py    # DB сесії
│   ├── models/           # ORM моделі
│   ├── schemas/          # Pydantic схеми
│   ├── services/         # Бізнес-логіка
│   └── main.py           # Точка входу
├── alembic/              # Міграції БД
├── .env                  # Налаштування (не в git!)
├── .env.example          # Приклад налаштувань
├── requirements.txt      # Залежності
└── README.md             # Цей файл
```

### Запуск в режимі розробки

```bash
# З автоперезавантаженням
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# З debug логами
DEBUG=true uvicorn app.main:app --reload
```

### Створення нової міграції

```bash
# Автогенерація міграції
alembic revision --autogenerate -m "опис_змін"

# Застосування міграції
alembic upgrade head

# Відкат останньої міграції
alembic downgrade -1
```

### Тестування API

```bash
# Логін
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Отримати список співробітників
curl http://localhost:8000/api/employees \
  -H "Authorization: Bearer YOUR_TOKEN"

# Health check
curl http://localhost:8000/health
```

---

## 📚 API Документація

### Інтерактивна документація

Після запуску сервера доступна на:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Основні endpoints

#### Автентифікація
- `POST /api/login` - Логін (отримати JWT токен)

#### Співробітники
- `GET /api/employees` - Список співробітників
- `POST /api/employees` - Створити співробітника
- `GET /api/employees/{id}` - Отримати співробітника
- `PATCH /api/employees/{id}` - Оновити співробітника

#### Події
- `GET /api/events` - Список подій
- `POST /api/events/manual` - Створити ручну подію (admin)
- `POST /api/terminal/scan` - Сканування NFC (від терміналу)

#### Статистика
- `GET /api/stats/employee/{id}` - Статистика співробітника
- `GET /api/stats/employee/{id}/daily` - Денна статистика

#### Графіки
- `GET /api/schedules` - Список графіків
- `POST /api/schedules` - Створити графік

#### Термінали
- `GET /api/terminals` - Список терміналів (admin)
- `POST /api/terminals` - Створити термінал (admin)

---

## 🗄 Міграції БД

### Основні команди

```bash
# Показати поточну версію
alembic current

# Показати історію міграцій
alembic history

# Застосувати всі міграції
alembic upgrade head

# Застосувати конкретну міграцію
alembic upgrade <revision>

# Відкотити до попередньої версії
alembic downgrade -1

# Відкотити всі міграції
alembic downgrade base

# Створити нову міграцію (автогенерація)
alembic revision --autogenerate -m "назва_міграції"

# Створити порожню міграцію
alembic revision -m "назва_міграції"
```

### Наявні міграції

1. **001_initial_schema.py** - Початкова схема БД
   - Таблиці: employees, terminals, events, schedules, users

2. **002_make_terminal_nullable.py** - terminal_id nullable
   - Дозволяє створювати ручні події без терміналу

3. **003_add_composite_index.py** - Складений індекс
   - Індекс (employee_id, ts) для швидких запитів

---

## 🚢 Deployment

### Docker (рекомендовано)

```bash
# Збірка образу
docker build -t timetracker-api .

# Запуск контейнера
docker run -d \
  --name timetracker \
  -p 8000:8000 \
  --env-file .env.production \
  timetracker-api

# З docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Systemd (Linux)

Створіть файл `/etc/systemd/system/timetracker.service`:

```ini
[Unit]
Description=TimeTracker API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/.venv/bin"
ExecStart=/path/to/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Активувати та запустити
sudo systemctl enable timetracker
sudo systemctl start timetracker
sudo systemctl status timetracker
```

### Nginx (reverse proxy)

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔧 Підтримка

### Логи

```bash
# Перегляд логів (якщо використовується systemd)
sudo journalctl -u timetracker -f

# Перегляд логів Docker
docker logs -f timetracker
```

### Backup бази даних

```bash
# MySQL backup
mysqldump -u timetracker -p timetracker > backup_$(date +%Y%m%d).sql

# Відновлення з backup
mysql -u timetracker -p timetracker < backup_20260126.sql
```

### Очищення старих подій

```python
# Створіть скрипт cleanup_old_events.py
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.event import Event

def cleanup_old_events(days=90):
    db = SessionLocal()
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(Event).filter(Event.ts < cutoff_date).delete()
    db.commit()
    print(f"Видалено {deleted} старих подій")
    db.close()

if __name__ == "__main__":
    cleanup_old_events()
```

### Моніторинг

Health check endpoint для моніторингу:

```bash
# Перевірка статусу
curl http://localhost:8000/health

# Очікувана відповідь
{"status":"ok","app":"TimeTracker API","env":"production","version":"1.0.0"}
```

---

## 🐛 Відомі проблеми та рішення

### Проблема: "Table 'users' doesn't exist"

**Рішення:** Застосуйте міграції
```bash
alembic upgrade head
```

### Проблема: "Column 'terminal_id' cannot be null"

**Рішення:** Застосуйте міграцію 002
```bash
alembic upgrade head
```

### Проблема: Повільні запити статистики

**Рішення:** Застосуйте міграцію 003 (складений індекс)
```bash
alembic upgrade head
```

### Проблема: Циркулярний імпорт

**Рішення:** Переконайтеся що `app/db/base.py` містить тільки Base, без імпортів моделей

---

## 📞 Контакти

- **Автор проєкту:** StelSuy
- **Email:** vinnik7898@gmail.com
- **GitHub:** https://github.com/StelSuy/diplom_v2

---

## 📄 Ліцензія

+

---

## 🙏 Подяки

- FastAPI за чудовий framework
- SQLAlchemy за потужний ORM
- Alembic за зручні міграції

---

**Версія:** 1.0.0  
**Останнє оновлення:** 26 січня 2026
