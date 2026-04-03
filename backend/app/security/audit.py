"""
Audit logger — writes to DB (audit_logs table).
Falls back to stderr if DB is unavailable.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal

_logger = logging.getLogger("audit")

_ACTION_LABELS: dict[str, str] = {
    "admin_login":          "Вхід в систему",
    "employee_create":      "Створення співробітника",
    "employee_update":      "Редагування співробітника",
    "employee_delete":      "Видалення співробітника",
    "user_create":          "Створення користувача",
    "user_update":          "Редагування користувача",
    "user_delete":          "Видалення користувача",
    "position_create":      "Створення посади",
    "position_update":      "Редагування посади",
    "position_delete":      "Видалення посади",
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
    admin_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    db: Session | None = None,
) -> None:
    """
    Записує аудит-подію в таблицю audit_logs.
    Якщо db не передано — відкриває власну сесію.
    """
    from app.models.audit_log import AuditLog

    details_json = json.dumps(details, ensure_ascii=False) if details else None

    entry = AuditLog(
        admin_id=admin_id,
        admin_username=admin_username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_json,
        created_at=datetime.now(timezone.utc),
    )

    _logger.info(
        f"[AUDIT] {admin_username} | {action} | {entity_type}:{entity_id} | {details_json}"
    )

    own_session = db is None
    session: Session = db or SessionLocal()
    try:
        session.add(entry)
        session.commit()
    except Exception as exc:
        session.rollback()
        _logger.error(f"[AUDIT] Failed to write audit log to DB: {exc}")
    finally:
        if own_session:
            session.close()


def get_action_types() -> list[dict]:
    return [{"action": k, "label": v} for k, v in _ACTION_LABELS.items()]
