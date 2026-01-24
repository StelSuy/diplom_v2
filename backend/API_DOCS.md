# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

Most endpoints require authentication using Bearer tokens.

### Get Access Token
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

Use this token in subsequent requests:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Employees

### List All Employees
```http
GET /api/employees
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "John Doe",
    "nfc_uid": "ABC123",
    "position": "Developer",
    "comment": "Senior developer",
    "is_active": true,
    "public_key_b64": null
  }
]
```

### Get Employee by ID
```http
GET /api/employees/{employee_id}
Authorization: Bearer <token>
```

### Create Employee
```http
POST /api/employees
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Jane Smith",
  "nfc_uid": "DEF456",
  "position": "Manager",
  "comment": "Optional comment"
}
```

### Update Employee
```http
PATCH /api/employees/{employee_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "position": "Senior Manager",
  "is_active": false
}
```

---

## Schedules

### Get Schedule for Date Range
```http
GET /api/schedule?date_from=2024-01-01&date_to=2024-01-31
Authorization: Bearer <token>
```

**Optional Parameters:**
- `employee_id` - Filter by specific employee

**Response:**
```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "items": [
    {
      "employee_id": 1,
      "day": "2024-01-15",
      "start_hhmm": "08:00",
      "end_hhmm": "17:00",
      "code": "ОФ"
    }
  ]
}
```

### Create/Update Schedule Cell
```http
POST /api/schedule/cell
Authorization: Bearer <token>
Content-Type: application/json

{
  "employee_id": 1,
  "day": "2024-01-15",
  "code": "5-7"
}
```

**Supported formats:**

1. **Short format** (hours only):
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "code": "5-7"
}
// Results in: 05:00 - 07:00
```

2. **Full format** (explicit time):
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "start_hhmm": "08:30",
  "end_hhmm": "17:30",
  "code": "ОФ"
}
```

3. **Clear cell** (delete):
```json
{
  "employee_id": 1,
  "day": "2024-01-15",
  "code": ""
}
```

### Delete Schedule Cell
```http
DELETE /api/schedule/cell?employee_id=1&day=2024-01-15
Authorization: Bearer <token>
```

### Export Schedule to PDF
```http
GET /api/schedule/pdf?date_from=2024-01-01&date_to=2024-01-31
Authorization: Bearer <token>
```

Returns PDF file with schedule table.

---

## Events

### Record NFC Event (Terminal)
```http
POST /api/nfc
X-Terminal-Key: <terminal_api_key>
Content-Type: application/json

{
  "nfc_uid": "ABC123",
  "direction": "IN",
  "ts": "2024-01-15T08:30:00Z",
  "terminal_name": "Terminal 1"
}
```

**Response:**
```json
{
  "ok": true,
  "event": {
    "id": 123,
    "employee_id": 1,
    "terminal_id": 1,
    "direction": "IN",
    "ts": "2024-01-15T08:30:00Z"
  },
  "employee": {
    "id": 1,
    "full_name": "John Doe"
  },
  "terminal": {
    "id": 1,
    "name": "Terminal 1"
  }
}
```

**Auto-direction logic:**
- If last event was IN → new event is OUT
- Otherwise → new event is IN

---

## Statistics

### Employee Work Time Stats
```http
GET /api/stats/employee/{employee_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "employee_id": 1,
  "total_minutes": 480,
  "total_hms": "08:00:00",
  "intervals": [
    {
      "in_utc": "2024-01-15T08:00:00Z",
      "out_utc": "2024-01-15T17:00:00Z",
      "in_local": "2024-01-15T09:00:00+01:00",
      "out_local": "2024-01-15T18:00:00+01:00",
      "minutes": 480,
      "auto_closed": false
    }
  ],
  "has_open_shift": false,
  "anomalies": [],
  "events": [...]
}
```

### Daily Statistics
```http
GET /api/stats/employee/{employee_id}/daily?from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <token>
```

**Response:**
```json
{
  "employee_id": 1,
  "from_date": "2024-01-01",
  "to_date": "2024-01-31",
  "total_minutes": 9600,
  "total_hms": "160:00:00",
  "items": [
    {
      "date_local": "2024-01-15",
      "worked_minutes": 480,
      "worked_seconds": 28800,
      "worked_hms": "08:00:00",
      "first_in_local": "2024-01-15T08:00:00+01:00",
      "last_out_local": "2024-01-15T17:00:00+01:00",
      "open_shift": false,
      "auto_closed": false,
      "anomalies": []
    }
  ],
  "weeks": [...],
  "months": [...]
}
```

---

## Terminals

### List Terminals
```http
GET /api/terminals
Authorization: Bearer <token>
```

### Create Terminal
```http
POST /api/terminals
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Terminal 2"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Terminal 2",
  "api_key": "trm_abc123def456..."
}
```

**⚠️ Important:** Save the `api_key` - it won't be shown again!

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid code format. Use 'H-H' (example: '5-7') or send start_hhmm/end_hhmm."
}
```

### 401 Unauthorized
```json
{
  "detail": "Missing Bearer token"
}
```

### 403 Forbidden
```json
{
  "detail": "Not allowed"
}
```

### 404 Not Found
```json
{
  "detail": "Employee not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "path": "/api/schedule/cell",
  "method": "POST"
}
```

---

## Rate Limiting

- Terminal scans: 1 per 5 seconds (configurable via `TERMINAL_SCAN_COOLDOWN_SECONDS`)
- Other endpoints: No limit currently (TODO: implement)

---

## Timezone Handling

All timestamps are stored in UTC but converted to Europe/Warsaw timezone for display.

**Formats:**
- Input: ISO 8601 with timezone or UTC assumed
- Output: Both UTC and local time provided
- Dates: Local Warsaw dates (YYYY-MM-DD)

---

## Testing with cURL

### Get token and use it:
```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/employees"
```

### Create schedule:
```bash
curl -X POST "http://localhost:8000/api/schedule/cell" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 1,
    "day": "2024-01-15",
    "code": "8-17"
  }'
```

---

## Interactive Documentation

Visit these URLs when server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration and testing.
