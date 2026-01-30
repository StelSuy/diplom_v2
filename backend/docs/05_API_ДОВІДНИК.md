# 📡 API ДОВІДНИК

**Дата оновлення:** 30 січня 2026  
**Версія API:** 1.0  
**Base URL:** `http://localhost:8000/api`

---

## 📋 ЗМІСТ

1. [Аутентифікація](#-аутентифікація)
2. [Співробітники](#-співробітники)
3. [Терміналі](#-терміналі)
4. [Події](#-події)
5. [Графіки роботи](#-графіки-роботи)
6. [Статистика](#-статистика)
7. [Коди помилок](#-коди-помилок)

---

## 🌐 ЗАГАЛЬНА ІНФОРМАЦІЯ

### Base URL
```
Development: http://localhost:8000/api
Production:  https://yourdomain.com/api
```

### Формат даних
- **Request:** JSON
- **Response:** JSON
- **Encoding:** UTF-8

### Заголовки

**Для всіх запитів:**
```
Content-Type: application/json
```

**Для захищених endpoint (після логіну):**
```
Authorization: Bearer <JWT_TOKEN>
```

**Для термінів:**
```
Authorization: Bearer <TERMINAL_API_KEY>
```

---

## 🔐 АУТЕНТИФІКАЦІЯ

### POST /auth/login

Отримати JWT токен для доступу до API.

**Request:**
```json
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid credentials"
}
```

**Приклад (cURL):**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Приклад (PowerShell):**
```powershell
$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Приклад (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)

token = response.json()["access_token"]
print(f"Token: {token}")
```

---

## 👥 СПІВРОБІТНИКИ

### GET /employees

Отримати список всіх співробітників.

**Request:**
```
GET /api/employees
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "full_name": "Іванов Іван Іванович",
    "nfc_uid": "A1B2C3D4",
    "position": "Менеджер",
    "is_active": true,
    "comment": null
  },
  {
    "id": 2,
    "full_name": "Петрова Марія Василівна",
    "nfc_uid": "E5F6G7H8",
    "position": "Бухгалтер",
    "is_active": true,
    "comment": null
  }
]
```

**Приклад (cURL):**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/api/employees \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /employees

Створити нового співробітника.

**Request:**
```json
POST /api/employees
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "full_name": "Сидоров Петро Олександрович",
  "nfc_uid": "I9J0K1L2",
  "position": "Інженер",
  "is_active": true,
  "comment": "Новий співробітник"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "full_name": "Сидоров Петро Олександрович",
  "nfc_uid": "I9J0K1L2",
  "position": "Інженер",
  "is_active": true,
  "comment": "Новий співробітник"
}
```

**Response (400 Bad Request) - дублікат NFC UID:**
```json
{
  "detail": "Employee with this NFC UID already exists"
}
```

**Приклад (Python):**
```python
import requests

headers = {"Authorization": f"Bearer {token}"}
data = {
    "full_name": "Сидоров Петро Олександрович",
    "nfc_uid": "I9J0K1L2",
    "position": "Інженер",
    "is_active": True
}

response = requests.post(
    "http://localhost:8000/api/employees",
    headers=headers,
    json=data
)

employee = response.json()
print(f"Створено співробітника ID: {employee['id']}")
```

---

### GET /employees/{id}

Отримати співробітника за ID.

**Request:**
```
GET /api/employees/1
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "full_name": "Іванов Іван Іванович",
  "nfc_uid": "A1B2C3D4",
  "position": "Менеджер",
  "is_active": true,
  "comment": null
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Employee not found"
}
```

---

### PUT /employees/{id}

Оновити дані співробітника.

**Request:**
```json
PUT /api/employees/1
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "full_name": "Іванов Іван Іванович",
  "position": "Старший менеджер",
  "is_active": true,
  "comment": "Підвищення"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "full_name": "Іванов Іван Іванович",
  "nfc_uid": "A1B2C3D4",
  "position": "Старший менеджер",
  "is_active": true,
  "comment": "Підвищення"
}
```

---

### DELETE /employees/{id}

Видалити співробітника.

**Request:**
```
DELETE /api/employees/1
Authorization: Bearer <JWT_TOKEN>
```

**Response (204 No Content)**

---

## 📟 ТЕРМІНАЛІ

### GET /terminals

Отримати список термінів.

**Request:**
```
GET /api/terminals
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Термінал 1",
    "location": "Вхід головний",
    "api_key": "terminal_abc123...",
    "is_active": true
  }
]
```

---

### POST /terminals

Створити новий термінал.

**Request:**
```json
POST /api/terminals
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "name": "Термінал 2",
  "location": "Офіс 2 поверх",
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "Термінал 2",
  "location": "Офіс 2 поверх",
  "api_key": "terminal_xyz789...",
  "is_active": true
}
```

---

### POST /register

Швидка реєстрація терміналу (без JWT токена).

**Request:**
```json
POST /api/register
Content-Type: application/json

{
  "name": "Термінал 3",
  "location": "Склад"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "name": "Термінал 3",
  "location": "Склад",
  "api_key": "terminal_def456...",
  "message": "Terminal registered successfully. Save the API key!"
}
```

**⚠️ ВАЖЛИВО:** Зберігайте `api_key` - він показується тільки один раз!

---

## 📅 ПОДІЇ

### POST /events/nfc

Реєстрація події з NFC терміналу (вхід/вихід).

**Request:**
```json
POST /api/events/nfc
Authorization: Bearer <TERMINAL_API_KEY>
Content-Type: application/json

{
  "nfc_uid": "A1B2C3D4",
  "direction": "IN",
  "ts": "2026-01-30T08:30:00"
}
```

**Параметри:**
- `nfc_uid` - NFC UID співробітника
- `direction` - `"IN"` (вхід) або `"OUT"` (вихід)
- `ts` - Час події (ISO 8601 format)

**Response (200 OK):**
```json
{
  "ok": true,
  "event": {
    "id": 123,
    "employee_id": 1,
    "terminal_id": 1,
    "direction": "IN",
    "ts": "2026-01-30T08:30:00"
  },
  "employee": {
    "id": 1,
    "full_name": "Іванов Іван Іванович"
  },
  "terminal": {
    "id": 1,
    "name": "Термінал 1"
  }
}
```

**Response (404 Not Found) - співробітник не знайдений:**
```json
{
  "detail": "Employee not found by nfc_uid"
}
```

**Response (400 Bad Request) - порушення cooldown:**
```json
{
  "detail": "Too soon after last event. Cooldown: 5s, actual: 2.1s"
}
```

**Response (400 Bad Request) - неправильна послідовність:**
```json
{
  "detail": "Cannot IN twice in a row. Last event was IN."
}
```

**Приклад (Arduino/ESP32):**
```cpp
#include <HTTPClient.h>
#include <ArduinoJson.h>

void sendEvent(String nfcUid, String direction) {
    HTTPClient http;
    http.begin("http://192.168.1.100:8000/api/events/nfc");
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", "Bearer terminal_abc123...");
    
    StaticJsonDocument<200> doc;
    doc["nfc_uid"] = nfcUid;
    doc["direction"] = direction;
    doc["ts"] = getCurrentTime(); // ISO 8601
    
    String json;
    serializeJson(doc, json);
    
    int httpCode = http.POST(json);
    
    if (httpCode == 200) {
        Serial.println("Event sent successfully");
    } else {
        Serial.printf("Error: %d\n", httpCode);
    }
    
    http.end();
}
```

---

### GET /events

Отримати список подій.

**Request:**
```
GET /api/events?skip=0&limit=100
Authorization: Bearer <JWT_TOKEN>
```

**Query параметри:**
- `skip` - Пропустити N записів (default: 0)
- `limit` - Кількість записів (default: 100, max: 1000)
- `employee_id` - Фільтр по співробітнику
- `terminal_id` - Фільтр по терміналу
- `date_from` - Фільтр від дати (ISO 8601)
- `date_to` - Фільтр до дати (ISO 8601)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 123,
      "employee_id": 1,
      "terminal_id": 1,
      "direction": "IN",
      "ts": "2026-01-30T08:30:00",
      "is_manual": false,
      "comment": null
    }
  ],
  "total": 1500,
  "skip": 0,
  "limit": 100
}
```

---

### POST /events/manual

Створити подію вручну (адміном).

**Request:**
```json
POST /api/events/manual
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "employee_id": 1,
  "direction": "IN",
  "ts": "2026-01-30T08:00:00",
  "comment": "Забув прикласти картку"
}
```

**Response (201 Created):**
```json
{
  "id": 124,
  "employee_id": 1,
  "terminal_id": null,
  "direction": "IN",
  "ts": "2026-01-30T08:00:00",
  "is_manual": true,
  "comment": "Забув прикласти картку",
  "created_by_user_id": 1
}
```

---

## 📊 ГРАФІКИ РОБОТИ

### GET /schedules

Отримати графіки роботи.

**Request:**
```
GET /api/schedules
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "18:00:00"
  }
]
```

**Примітка:** `day_of_week`: 1=Понеділок, 7=Неділя

---

### POST /schedules

Створити графік роботи.

**Request:**
```json
POST /api/schedules
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "employee_id": 1,
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "18:00:00"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "employee_id": 1,
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "18:00:00"
}
```

---

## 📈 СТАТИСТИКА

### GET /stats/worktime

Робочий час співробітників за період.

**Request:**
```
GET /api/stats/worktime?start_date=2026-01-01&end_date=2026-01-31&employee_id=1
Authorization: Bearer <JWT_TOKEN>
```

**Query параметри:**
- `start_date` - Початкова дата (YYYY-MM-DD)
- `end_date` - Кінцева дата (YYYY-MM-DD)
- `employee_id` - ID співробітника (опціонально)

**Response (200 OK):**
```json
[
  {
    "employee_id": 1,
    "employee_name": "Іванов Іван Іванович",
    "date": "2026-01-30",
    "first_in": "2026-01-30T08:30:00",
    "last_out": "2026-01-30T17:45:00",
    "total_hours": 9.25,
    "breaks": [
      {
        "start": "2026-01-30T12:00:00",
        "end": "2026-01-30T13:00:00",
        "duration_minutes": 60
      }
    ]
  }
]
```

---

## ❌ КОДИ ПОМИЛОК

### HTTP Status Codes

| Код | Значення | Опис |
|-----|----------|------|
| 200 | OK | Запит виконано успішно |
| 201 | Created | Ресурс створено |
| 204 | No Content | Успішно, без тіла відповіді |
| 400 | Bad Request | Невалідні дані |
| 401 | Unauthorized | Не авторизовано (немає токена або невалідний) |
| 403 | Forbidden | Доступ заборонено |
| 404 | Not Found | Ресурс не знайдено |
| 422 | Unprocessable Entity | Помилка валідації |
| 500 | Internal Server Error | Внутрішня помилка сервера |

### Формат помилок

```json
{
  "detail": "Опис помилки"
}
```

**Або для валідації:**
```json
{
  "detail": [
    {
      "loc": ["body", "nfc_uid"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🧪 ТЕСТУВАННЯ API

### Через Swagger UI (рекомендовано)

1. Відкрити: http://localhost:8000/docs
2. Натиснути "Authorize"
3. Ввести JWT токен (отримати через `/auth/login`)
4. Тестувати endpoints через інтерфейс

### Через Postman

1. Створити нову колекцію "TimeTracker API"
2. Додати змінну `{{base_url}}` = `http://localhost:8000/api`
3. Додати змінну `{{token}}` = отриманий JWT токен
4. Для кожного запиту додати Header:
   ```
   Authorization: Bearer {{token}}
   ```

### Через Python

```python
import requests

# Базовий URL
BASE_URL = "http://localhost:8000/api"

# Логін
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# Headers для наступних запитів
headers = {"Authorization": f"Bearer {token}"}

# Отримати співробітників
employees = requests.get(f"{BASE_URL}/employees", headers=headers).json()
print(f"Співробітників: {len(employees)}")

# Створити подію
event_data = {
    "nfc_uid": "A1B2C3D4",
    "direction": "IN",
    "ts": "2026-01-30T08:30:00"
}
# Примітка: для events/nfc потрібен terminal API key, а не JWT
```

---

## 📚 ДОДАТКОВІ РЕСУРСИ

### Автоматична документація:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Health Check:

```
GET /health
```

Не потребує аутентифікації. Перевіряє чи працює API.

**Response:**
```json
{
  "status": "ok",
  "app": "TimeTracker API",
  "env": "development",
  "version": "1.0.0"
}
```

---

**Оновлено:** 30 січня 2026  
**Версія документації:** 2.0
