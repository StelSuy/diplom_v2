# 🚀 Быстрый старт - TimeTracker Backend

## За 5 минут до работы

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения
```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env (минимум - укажите DATABASE_URL)
nano .env
```

**Обязательно настройте:**
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/timetracker
```

### 3. Инициализация базы данных
```bash
python init_db.py
```

### 4. Запуск сервера
```bash
# Windows
run_dev.bat

# Linux/Mac
./run_dev.sh

# Или напрямую
uvicorn app.main:app --reload
```

### 5. Проверка работы
Откройте браузер: **http://localhost:8000/docs**

---

## Первые шаги

### 1. Получить токен авторизации
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Сохраните `access_token` из ответа.

### 2. Получить список сотрудников
```bash
curl "http://localhost:8000/api/employees" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Создать график на день
```bash
curl -X POST "http://localhost:8000/api/schedule/cell" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 1,
    "day": "2024-01-15",
    "code": "8-17"
  }'
```

### 4. Получить статистику
```bash
curl "http://localhost:8000/api/stats/employee/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Структура проекта

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── deps.py       # Dependencies (auth, db)
│   │   ├── router.py     # Main router
│   │   └── routes/       # Route handlers
│   │       ├── auth.py
│   │       ├── employees.py
│   │       ├── events.py
│   │       ├── schedules.py
│   │       ├── stats.py
│   │       └── terminals.py
│   │
│   ├── core/             # Core functionality
│   │   ├── config.py     # Settings
│   │   ├── security.py   # JWT, passwords
│   │   ├── logging.py    # Logging setup
│   │   └── time.py       # Timezone utils
│   │
│   ├── crud/             # Database operations
│   │   ├── employee.py
│   │   ├── event.py
│   │   ├── schedule.py
│   │   └── terminal.py
│   │
│   ├── db/               # Database config
│   │   ├── base.py       # Base class
│   │   ├── session.py    # Session factory
│   │   └── init_db.py    # DB initialization
│   │
│   ├── models/           # SQLAlchemy models
│   │   ├── employee.py
│   │   ├── event.py
│   │   ├── schedule.py
│   │   └── terminal.py
│   │
│   ├── schemas/          # Pydantic schemas
│   │   ├── auth.py
│   │   ├── employee.py
│   │   ├── event.py
│   │   ├── schedule.py
│   │   └── stats.py
│   │
│   ├── services/         # Business logic
│   │   └── worktime.py
│   │
│   ├── security/         # Security utils
│   │   └── verify.py
│   │
│   ├── static/           # Admin panel
│   └── main.py           # FastAPI app
│
├── alembic/              # Database migrations
│   ├── versions/
│   └── env.py
│
├── .env.example          # Environment template
├── requirements.txt      # Python packages
├── init_db.py           # DB initialization script
├── health_check.py      # Health check script
├── README.md            # Main documentation
├── API_DOCS.md          # API documentation
└── FAQ.md               # Frequently asked questions
```

---

## Основные команды

```bash
# Установка
pip install -r requirements.txt

# Инициализация БД
python init_db.py

# Проверка здоровья системы
python health_check.py

# Запуск dev сервера
uvicorn app.main:app --reload

# Создание миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

---

## Полезные ссылки

После запуска сервера:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:8000/admin

---

## Что дальше?

1. **Прочитайте документацию**:
   - `README.md` - общая информация
   - `API_DOCS.md` - подробное описание API
   - `FAQ.md` - решение частых проблем

2. **Измените пароли**:
   ```env
   ADMIN_PASSWORD=новый_надёжный_пароль
   JWT_SECRET=случайный_секретный_ключ
   ```

3. **Протестируйте API**:
   - Используйте Swagger UI
   - Или curl примеры из API_DOCS.md

4. **Настройте для production**:
   - HTTPS
   - Реальную БД
   - Логирование в файлы
   - Мониторинг

---

## Решение проблем

### Сервер не запускается
```bash
# Проверьте зависимости
pip install -r requirements.txt

# Проверьте .env
cat .env

# Проверьте подключение к БД
python health_check.py
```

### График не сохраняется
```bash
# Включите debug
echo "DEBUG=true" >> .env

# Перезапустите сервер
# Смотрите логи в консоли

# Проверьте формат запроса (см. FAQ.md)
```

### Ошибка авторизации
```bash
# Получите новый токен
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## Поддержка

- 📖 Документация: `README.md`, `API_DOCS.md`, `FAQ.md`
- 🔍 Логи: смотрите вывод в консоли при `DEBUG=true`
- 🏥 Диагностика: `python health_check.py`
- 📊 API тестирование: http://localhost:8000/docs

**Успешного использования!** 🎉
