# ⚡ Быстрый старт - Backend

## 🚀 Запуск сервера

```bash
# Windows
run_dev.bat

# Linux/Mac
./run_dev.sh

# Или напрямую
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер запустится на: **http://localhost:8000**

---

## 🔐 Быстрое тестирование API

### 1️⃣ Получить токен
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Ответ:**
```json
{"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."}
```

### 2️⃣ Сохранить расписание (одна ячейка)
```bash
curl -X POST http://localhost:8000/api/schedule \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ваш_токен>" \
  -d '{
    "cells": [
      {"employee_id": 1, "day": "2026-01-02", "code": "8-17"}
    ]
  }'
```

### 3️⃣ Получить расписание
```bash
curl -X GET "http://localhost:8000/api/schedule?date_from=2026-01-01&date_to=2026-01-31&employee_id=1" \
  -H "Authorization: Bearer <ваш_токен>"
```

---

## 📚 Полезные ссылки

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Admin Panel:** http://localhost:8000/admin

---

## 🔍 Просмотр логов

Логи выводятся в консоль. Для фильтрации:

```bash
# Только ошибки
uvicorn app.main:app --log-level error

# Детальный debug
uvicorn app.main:app --log-level debug
```

---

## 📝 Частые команды

### Проверить подключение к БД
```bash
curl http://localhost:8000/health
```

### Список всех роутов
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

### Создать сотрудника
```bash
curl -X POST http://localhost:8000/api/employees/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Іван Петренко",
    "nfc_uid": "ABC12345",
    "position": "Менеджер"
  }'
```

### Получить всех сотрудников
```bash
curl http://localhost:8000/api/employees/
```

---

## 🐛 Решение проблем

### Ошибка: Cannot connect to database
**Решение:**
1. Проверьте `.env` файл
2. Убедитесь что MySQL/MariaDB запущена
3. Проверьте DATABASE_URL

### Ошибка: 401 Unauthorized
**Решение:**
1. Получите новый токен через `/api/auth/login`
2. Убедитесь что токен в заголовке `Authorization: Bearer <token>`

### Ошибка: 405 Method Not Allowed
**Решение:**
- Проверьте метод запроса (GET/POST/PUT/DELETE)
- Убедитесь что используете правильный endpoint

### Ошибка: ModuleNotFoundError
**Решение:**
```bash
pip install -r requirements.txt
```

---

## 📦 Обновление зависимостей

```bash
pip install --upgrade -r requirements.txt
```

---

## 🧪 Запуск тестов (когда будут)

```bash
pytest tests/ -v
```

---

**Подробнее:** См. файлы IMPROVEMENTS.md, FIX_405_DONE.md, TESTING_CHECKLIST.md
