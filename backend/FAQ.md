# FAQ - Часто задаваемые вопросы

## Установка и запуск

### Q: Как установить зависимости?
```bash
pip install -r requirements.txt
```

### Q: Как создать .env файл?
```bash
cp .env.example .env
# Затем отредактируйте .env под свои нужды
```

### Q: Как инициализировать базу данных?
```bash
python init_db.py
```

Или с помощью Alembic:
```bash
alembic upgrade head
```

### Q: Как запустить сервер для разработки?
**Windows:**
```bash
run_dev.bat
```

**Linux/Mac:**
```bash
./run_dev.sh
```

Или напрямую:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## График работы (Schedules)

### Q: График не сохраняется в БД. Что делать?

**Проверьте следующее:**

1. **Проверьте формат данных:**
   - Код должен быть в формате "H-H" (например "5-7", "08-17")
   - ИЛИ нужно передавать start_hhmm И end_hhmm

2. **Проверьте логи сервера:**
   ```bash
   # Должны видеть:
   INFO [app.api.routes.schedules] Upserting schedule cell: employee=1, day=2024-01-15, code=5-7
   INFO [app.api.routes.schedules] Schedule cell saved: id=1, start=05:00, end=07:00
   ```

3. **Проверьте ответ от сервера:**
   - Статус 200 = успешно сохранено
   - Статус 400 = ошибка валидации (читайте `detail` в ответе)
   - Статус 500 = ошибка сервера (проверьте логи)

4. **Проверьте БД напрямую:**
   ```sql
   SELECT * FROM schedules WHERE employee_id = 1 AND day = '2024-01-15';
   ```

### Q: Какие форматы кода поддерживаются?

**Формат 1: Только часы (H-H)**
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "code": "5-7"
}
```
Результат: 05:00 - 07:00

**Формат 2: Полный формат (с явным временем)**
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "start_hhmm": "08:30",
  "end_hhmm": "17:30",
  "code": "ОФ"
}
```

**Формат 3: Очистка ячейки**
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "code": ""
}
```

### Q: Как удалить график на определённую дату?

Есть два способа:

1. **Через POST с пустым кодом:**
```bash
curl -X POST "http://localhost:8000/api/schedule/cell" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1, "day": "2024-01-15", "code": ""}'
```

2. **Через DELETE:**
```bash
curl -X DELETE "http://localhost:8000/api/schedule/cell?employee_id=1&day=2024-01-15" \
  -H "Authorization: Bearer $TOKEN"
```

---

## События (Events)

### Q: События дублируются. Что делать?

Проверьте настройку cooldown в `.env`:
```env
TERMINAL_SCAN_COOLDOWN_SECONDS=5
```

Это предотвратит создание событий чаще чем раз в 5 секунд.

### Q: Как работает авто-определение направления (IN/OUT)?

Логика простая:
- Если последнее событие было **IN** → новое будет **OUT**
- Во всех остальных случаях → новое будет **IN**

Это работает автоматически на сервере, терминал может отправлять любое direction.

### Q: Что означает "auto_closed" в интервалах?

Если сотрудник не сделал OUT-событие, система автоматически закроет смену в конце дня (23:59:59 по Warsaw времени).

---

## Авторизация

### Q: Как получить токен для API?

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Ответ:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Q: Как использовать токен в запросах?

Добавьте заголовок:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Q: Токен истекает?

Да, через 60 минут (по умолчанию). Можно изменить в `.env`:
```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Q: Где хранится пароль админа?

В `.env` файле:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

**⚠️ ВАЖНО:** Измените пароль для production!

---

## База данных

### Q: Какие БД поддерживаются?

- MySQL / MariaDB (рекомендуется)
- PostgreSQL (нужно изменить драйвер в DATABASE_URL)
- SQLite (только для разработки)

### Q: Как настроить подключение к БД?

В `.env`:
```env
# MySQL/MariaDB
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/timetracker

# PostgreSQL
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/timetracker

# SQLite (для тестов)
DATABASE_URL=sqlite:///./timetracker.db
```

### Q: Как создать миграцию при изменении моделей?

```bash
# Автогенерация миграции
alembic revision --autogenerate -m "Add new field"

# Применить миграцию
alembic upgrade head
```

### Q: Как откатить миграцию?

```bash
# Откат на одну версию назад
alembic downgrade -1

# Откат до конкретной ревизии
alembic downgrade <revision_id>
```

### Q: Как посмотреть текущую версию БД?

```bash
alembic current
```

---

## Терминалы

### Q: Как создать новый терминал?

```bash
curl -X POST "http://localhost:8000/api/terminals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Terminal Entrance"}'
```

Ответ:
```json
{
  "id": 1,
  "name": "Terminal Entrance",
  "api_key": "trm_abc123def456..."
}
```

**⚠️ ВАЖНО:** Сохраните `api_key` - он больше не будет показан!

### Q: Как терминал отправляет события?

```bash
curl -X POST "http://localhost:8000/api/nfc" \
  -H "X-Terminal-Key: trm_abc123def456..." \
  -H "Content-Type: application/json" \
  -d '{
    "nfc_uid": "ABC123",
    "direction": "IN",
    "ts": "2024-01-15T08:30:00Z",
    "terminal_name": "Terminal 1"
  }'
```

---

## Логирование и отладка

### Q: Как включить подробное логирование?

В `.env`:
```env
DEBUG=true
SQL_ECHO=1
```

### Q: Где смотреть логи?

Логи выводятся в консоль (stdout). Для продакшена настройте запись в файлы.

### Q: Как отладить проблему с API?

1. Включите DEBUG режим
2. Смотрите логи в консоли
3. Используйте Swagger UI: http://localhost:8000/docs
4. Проверьте Network tab в браузере (F12)

---

## Производительность

### Q: Как настроить пул подключений к БД?

В `.env`:
```env
DB_POOL_SIZE=10          # Размер пула
DB_MAX_OVERFLOW=20       # Максимум дополнительных подключений
DB_POOL_RECYCLE=1800     # Переиспользование соединений (секунды)
```

### Q: API медленно работает. Что делать?

1. Проверьте индексы в БД (запустите `python health_check.py`)
2. Включите кэширование (TODO: не реализовано)
3. Используйте connection pooling
4. Оптимизируйте запросы (N+1 проблемы)

---

## Безопасность

### Q: Как изменить JWT секрет?

В `.env`:
```env
JWT_SECRET=ваш-очень-длинный-случайный-секрет-ключ
```

Сгенерировать можно так:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Q: Как настроить CORS для production?

В `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

### Q: Нужен ли HTTPS?

**Да!** Для production обязательно используйте HTTPS. Настройте через:
- Nginx reverse proxy
- Traefik
- Или облачный балансировщик

---

## Тестирование

### Q: Есть ли тесты?

Пока нет. TODO: добавить pytest тесты.

### Q: Как протестировать API?

1. **Swagger UI**: http://localhost:8000/docs
2. **cURL** (примеры в API_DOCS.md)
3. **Postman** (TODO: создать коллекцию)
4. **Python requests**:
```python
import requests
resp = requests.post("http://localhost:8000/api/auth/login",
                     json={"username": "admin", "password": "admin123"})
token = resp.json()["access_token"]
```

---

## Развёртывание (Deployment)

### Q: Как запустить в production?

1. **Используйте gunicorn** вместо uvicorn:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Или используйте systemd service**
3. **Настройте Nginx** как reverse proxy
4. **Включите HTTPS**

### Q: Как создать Docker контейнер?

TODO: Добавить Dockerfile и docker-compose.yml

### Q: Где хранить логи в production?

Настройте запись в файлы вместо stdout:
```python
# В app/core/logging.py
handler = logging.FileHandler("/var/log/timetracker/app.log")
```

---

## Дополнительная помощь

### Q: Где найти больше информации?

- **API Documentation**: `API_DOCS.md`
- **Changelog**: `CHANGELOG.md`
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Q: Как сообщить об ошибке?

1. Проверьте что это не известная проблема (FAQ)
2. Соберите логи с DEBUG=true
3. Опишите шаги для воспроизведения
4. Укажите версию Python и используемую ОС

### Q: Как предложить улучшение?

Создайте issue с описанием:
- Что хотите улучшить
- Зачем это нужно
- Как это должно работать
