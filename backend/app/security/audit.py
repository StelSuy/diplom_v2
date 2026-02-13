"""
Audit logger for admin actions.

Writes structured audit entries to:
  - stdout (via logging)
  - in-memory ring buffer (MAX_ENTRIES) — доступний через get_audit_log()
"""
import logging
import json
from collections import deque
from datetime import datetime, timezone
from threading import Lock

_audit_logger = logging.getLogger("audit")

if not _audit_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("[AUDIT] %(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    _audit_logger.addHandler(_handler)
    _audit_logger.setLevel(logging.INFO)
    _audit_logger.propagate = False

# In-memory ring buffer — останні 500 записів
MAX_ENTRIES = 500
_log_buffer: deque[dict] = deque(maxlen=MAX_ENTRIES)
_buffer_lock = Lock()

# Людські назви дій
_ACTION_LABELS: dict[str, str] = {
    "admin_login":          "Вхід в систему",
    "employee_create":      "Створення співробітника",
    "employee_update":      "Редагування співробітника",
    "employee_delete":      "Видалення співробітника",
    "manual_event_create":  "Ручне додавання події",
    "manual_event_delete":  "Видалення ручної події",
    "clear_day_events":     "Очищення подій за день",
    "terminal_create":      "Створення терміналу",
    "terminal_rotate_key":  "Зміна ключа терміналу",
}


def audit_log(
    action: str,
    admin_username: str,
    *,
    details: dict | None = None,
):
    """
    Log an auditable admin action.

    Args:
        action: e.g. "manual_event_create", "employee_delete", "terminal_rotate_key"
        admin_username: who performed the action
        details: extra data (employee_id, event_id, etc.)
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "action_label": _ACTION_LABELS.get(action, action),
        "admin": admin_username,
        "details": details or {},
    }

    _audit_logger.info(json.dumps(entry, ensure_ascii=False))

    with _buffer_lock:
        _log_buffer.appendleft(entry)  # найновіші — спереду


def get_audit_log(
    limit: int = 100,
    action_filter: str | None = None,
) -> list[dict]:
    """
    Повертає останні записи аудиту з in-memory буфера.

    Args:
        limit: максимальна кількість записів (1..500)
        action_filter: якщо задано — тільки записи з цим action
    """
    with _buffer_lock:
        entries = list(_log_buffer)

    if action_filter:
        entries = [e for e in entries if e.get("action") == action_filter]

    return entries[:limit]


def get_action_types() -> list[dict]:
    """Повертає список відомих типів дій для фільтру."""
    return [
        {"action": k, "label": v}
        for k, v in _ACTION_LABELS.items()
    ]
