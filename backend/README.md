# 🕐 TimeTracker API

**Система обліку робочого часу з NFC терміналами**

---

## 📖 Опис

TimeTracker API - це сучасна backend система для автоматизованого обліку робочого часу співробітників з використанням NFC терміналів. Система забезпечує:

- ✅ Автоматичну реєстрацію входу/виходу через NFC картки
- ✅ Управління співробітниками та термінами
- ✅ Статистику робочого часу
- ✅ REST API для інтеграції
- ✅ Адмін панель для управління

---

## 🚀 Швидкий старт

### 1. Вимоги

- Python 3.12+
- MySQL 8.0+ або MariaDB 11+
- Git

### 2. Запуск

```powershell
# Клонувати репозиторій
git clone <repository-url>
cd backend

# Створити віртуальне оточення
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Встановити залежності
pip install -r requirements.txt

# Налаштувати .env
copy .env.example .env
# Відредагувати .env файл

# Застосувати міграції
alembic upgrade head

# Запустити сервер
uvicorn app.main:app --reload
```

### 3. Перевірка

Відкрити в браузері:
- API: http://localhost:8000
- Документація: http://localhost:8000/docs

---

## 📚 Документація

**📁 Вся документація знаходиться в директорії `docs/`**

### Основні документи:

1. **[00_ЗМІСТ.md](docs/00_ЗМІСТ.md)** - Зміст та навігація по документації
2. **[01_ШВИДКИЙ_СТАРТ.md](docs/01_ШВИДКИЙ_СТАРТ.md)** - Детальна інструкція запуску
3. **[02_DEPLOYMENT_НА_СЕРВЕР.md](docs/02_DEPLOYMENT_НА_СЕРВЕР.md)** - Deployment на production
4. **[03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md](docs/03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md)** - Робота з MySQL
5. **[05_API_ДОВІДНИК.md](docs/05_API_ДОВІДНИК.md)** - API endpoints та приклади

### Швидкі посилання:

- 🚀 **Для локального запуску:** [01_ШВИДКИЙ_СТАРТ.md](docs/01_ШВИДКИЙ_СТАРТ.md)
- 🌐 **Для deployment:** [02_DEPLOYMENT_НА_СЕРВЕР.md](docs/02_DEPLOYMENT_НА_СЕРВЕР.md)
- 🗄️ **Для роботи з БД:** [03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md](docs/03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md)

---

## 🏗️ Технологічний стек

### Backend
- **FastAPI** - Сучасний async веб-фреймворк
- **SQLAlchemy 2.0** - ORM для роботи з БД
- **Alembic** - Міграції бази даних
- **Pydantic V2** - Валідація даних
- **JWT** - Аутентифікація
- **Bcrypt** - Хешування паролів

### База даних
- **MySQL 8.0+** або **MariaDB 11+**

### Deployment (опціонально)
- **Docker** - Контейнеризація
- **Nginx** - Reverse proxy
- **Let's Encrypt** - SSL сертифікати

---

## 📁 Структура проекту

```
backend/
├── app/                      # Основний код застосунку
│   ├── api/                  # API endpoints
│   ├── core/                 # Конфігурація та безпека
│   ├── crud/                 # CRUD операції
│   ├── db/                   # База даних
│   ├── models/               # SQLAlchemy моделі
│   ├── schemas/              # Pydantic схеми
│   ├── services/             # Бізнес-логіка
│   └── main.py               # Точка входу
├── alembic/                  # Міграції БД
├── docs/                     # Документація (УКР)
├── .env                      # Змінні оточення
├── requirements.txt          # Python залежності
└── README.md                 # Цей файл
```

---

## 🔐 Безпека

### Development

```ini
# .env
DEBUG=true
JWT_SECRET=будь-що-довше-32-символів
ADMIN_PASSWORD=admin123
ALLOWED_ORIGINS=*
```

### Production

```ini
# .env.production
DEBUG=false
JWT_SECRET=ДУЖЕ_ДОВГИЙ_СЕКРЕТ_64_СИМВОЛИ_ТА_БІЛЬШЕ
ADMIN_PASSWORD=СИЛЬНИЙ_ПАРОЛЬ_З_ЦИФРАМИ_123!@#
ALLOWED_ORIGINS=https://yourdomain.com
```

**⚠️ ВАЖЛИВО:**
- Згенеруйте унікальний `JWT_SECRET`: `openssl rand -hex 64`
- Змініть `ADMIN_PASSWORD` на сильний пароль
- Вкажіть конкретні домени в `ALLOWED_ORIGINS`

---

## 📡 API Endpoints

### Аутентифікація
```
POST /api/auth/login - Логін (отримати JWT токен)
```

### Співробітники
```
GET    /api/employees     - Список
POST   /api/employees     - Створити
GET    /api/employees/:id - Отримати
PUT    /api/employees/:id - Оновити
DELETE /api/employees/:id - Видалити
```

### Події
```
POST /api/events/nfc    - Реєстрація з терміналу
GET  /api/events        - Список
POST /api/events/manual - Ручне створення
```

### Терміналі
```
GET  /api/terminals - Список
POST /api/terminals - Створити
POST /api/register  - Швидка реєстрація
```

**📖 Детальна документація:** [05_API_ДОВІДНИК.md](docs/05_API_ДОВІДНИК.md)

---

## 🧪 Тестування

### Через Swagger UI (рекомендовано)
```
http://localhost:8000/docs
```

### Через cURL
```bash
# Логін
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Health check
curl http://localhost:8000/health
```

### Через Python
```python
import requests

# Логін
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Отримати співробітників
headers = {"Authorization": f"Bearer {token}"}
employees = requests.get(
    "http://localhost:8000/api/employees",
    headers=headers
).json()
```

---

## 🗄️ База даних

### Створення БД

```sql
CREATE DATABASE diploma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'timetracker'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON diploma_db.* TO 'timetracker'@'localhost';
FLUSH PRIVILEGES;
```

### Міграції

```powershell
# Застосувати всі міграції
alembic upgrade head

# Створити нову міграцію
alembic revision --autogenerate -m "опис"

# Відкотити останню
alembic downgrade -1
```

### Backup

```powershell
# Створити backup
mysqldump -u timetracker -ppassword diploma_db > backup.sql

# Відновити
mysql -u timetracker -ppassword diploma_db < backup.sql
```

**📖 Детальна документація:** [03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md](docs/03_УПРАВЛІННЯ_БАЗОЮ_ДАНИХ.md)

---

## 🚀 Deployment

### Без Docker (простіше)

1. Налаштувати Linux сервер (Ubuntu 22.04)
2. Встановити Python 3.12 та MySQL
3. Клонувати проект
4. Налаштувати .env
5. Застосувати міграції
6. Налаштувати systemd сервіс
7. Налаштувати Nginx
8. Отримати SSL сертифікат

### З Docker (рекомендовано)

```bash
# Налаштувати .env.production
cp .env.production.example .env.production
nano .env.production

# Запустити
docker compose -f docker-compose.prod.yml up -d

# Перевірити
curl https://yourdomain.com/health
```

**📖 Детальна документація:** [02_DEPLOYMENT_НА_СЕРВЕР.md](docs/02_DEPLOYMENT_НА_СЕРВЕР.md)

---

## 💾 Управління

### Корисні команди

```powershell
# Запустити development сервер
uvicorn app.main:app --reload

# Очистити кеш
.\clear_cache.bat

# Backup БД
.\auto_backup.ps1

# Перевірити логи
# Логи виводяться в консоль uvicorn
```

### Структура логів

```
INFO:     127.0.0.1:54321 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:54322 - "POST /api/auth/login HTTP/1.1" 200 OK
```

---

## 🔍 Розв'язання проблем

### MySQL не запущений
```powershell
Get-Service MySQL*
Start-Service MySQL80
```

### База не існує
```sql
CREATE DATABASE diploma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Порт 8000 зайнятий
```powershell
# Знайти процес
netstat -ano | findstr :8000

# Вбити або використати інший порт
uvicorn app.main:app --port 8001 --reload
```

### Модуль не знайдено
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**📖 Повний troubleshooting:** [01_ШВИДКИЙ_СТАРТ.md](docs/01_ШВИДКИЙ_СТАРТ.md) → Типові проблеми

---

## 📞 Підтримка

### Документація
- 📁 **Вся документація:** [docs/](docs/)
- 📖 **Зміст:** [docs/00_ЗМІСТ.md](docs/00_ЗМІСТ.md)

### Автоматична документація API
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Health Check
- **Endpoint:** http://localhost:8000/health

---

## 📊 Статус проекту

- ✅ **Версія:** 1.0.0
- ✅ **Статус:** Production Ready
- ✅ **Python:** 3.12+
- ✅ **Framework:** FastAPI
- ✅ **База даних:** MySQL 8.0+
- ✅ **Документація:** Повна (УКР)

---

## 🎯 Roadmap

### Версія 1.1 (Заплановано)
- [ ] Unit тести (pytest)
- [ ] Пагінація для списків
- [ ] Rate limiting
- [ ] Кешування (Redis)

### Версія 2.0 (Майбутнє)
- [ ] WebSocket для real-time
- [ ] Експорт звітів (PDF/Excel)
- [ ] Email нотифікації
- [ ] Мобільний додаток

---

## ⚖️ Ліцензія

Proprietary - Для внутрішнього використання

---

## 👥 Автори

**Проект:** TimeTracker API  
**Розробка:** StelSuy
**Документація:** Claude (Anthropic)  
**Дата:** 30 січня 2026


**Бажаємо успіхів у використанні TimeTracker API! 🚀**

**Наступний крок:** [docs/01_ШВИДКИЙ_СТАРТ.md](docs/01_ШВИДКИЙ_СТАРТ.md)
