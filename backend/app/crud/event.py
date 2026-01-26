from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, timezone
import logging

from app.core.time import ensure_utc
from app.core.config import settings
from app.models.event import Event
from app.models.employee import Employee
from app.schemas.terminal import TerminalScanRequest

logger = logging.getLogger(__name__)


def get_last_event_for_employee(db: Session, employee_id: int, lock: bool = False) -> Event | None:
    """
    Получить последнее событие сотрудника.
    
    Args:
        db: Database session
        employee_id: ID сотрудника
        lock: Использовать SELECT FOR UPDATE для блокировки (при race conditions)
    
    Returns:
        Последнее событие или None
    """
    query = (
        db.query(Event)
        .filter(Event.employee_id == employee_id)
        .order_by(desc(Event.ts))
    )
    
    if lock:
        query = query.with_for_update()
    
    return query.first()


def create_event(
    db: Session,
    employee_id: int,
    terminal_id: int,
    direction: str,
    ts,
) -> Event:
    """
    Базовое создание события.
    
    Args:
        db: Database session
        employee_id: ID сотрудника
        terminal_id: ID терминала (Integer)
        direction: 'IN' или 'OUT'
        ts: timestamp события
    
    Returns:
        Created Event object
    """
    direction = direction.upper().strip()
    if direction not in ("IN", "OUT"):
        raise ValueError("direction must be IN or OUT")

    ts_utc = ensure_utc(ts)
    
    # Убеждаемся что terminal_id это int
    if not isinstance(terminal_id, int):
        try:
            terminal_id = int(terminal_id)
        except (ValueError, TypeError):
            raise ValueError(f"terminal_id must be an integer, got {type(terminal_id)}")

    logger.info(f"Creating event: employee={employee_id}, terminal={terminal_id}, direction={direction}")
    
    ev = Event(
        employee_id=employee_id,
        terminal_id=terminal_id,
        direction=direction,
        ts=ts_utc,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    
    logger.info(f"Event created: id={ev.id}")
    return ev


def list_events_for_employee(db: Session, employee_id: int) -> list[Event]:
    """Получить все события сотрудника"""
    return (
        db.query(Event)
        .filter(Event.employee_id == employee_id)
        .order_by(asc(Event.ts))
        .all()
    )


def create_event_from_terminal_scan(db: Session, payload: TerminalScanRequest) -> dict:
    """
    Создание события от терминала с авто-определением направления.
    
    Логика:
    - Если последнее событие было IN -> новое OUT
    - Иначе -> новое IN
    
    Args:
        db: Database session
        payload: TerminalScanRequest с данными от терминала
    
    Returns:
        dict с информацией о созданном событии или сообщением о cooldown
    """
    uid = payload.uid.strip().upper()
    terminal_id = int(payload.terminal_id)

    employee = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if not employee:
        raise ValueError("Unknown UID (employee not registered)")

    # ts из Android: миллисекунды -> datetime UTC
    ts_ms = int(payload.ts)
    ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    ts_utc = ensure_utc(ts_dt)

    # ИСПРАВЛЕНИЕ: Используем блокировку для предотвращения race condition
    last = get_last_event_for_employee(db, employee.id, lock=True)

    # Cooldown проверка
    cooldown_sec = int(getattr(settings, "terminal_scan_cooldown_seconds", 0) or 0)
    if cooldown_sec > 0 and last:
        last_ts = last.ts
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        else:
            last_ts = last_ts.astimezone(timezone.utc)

        delta = (ts_utc - last_ts).total_seconds()
        if delta < cooldown_sec:
            wait_left = int(cooldown_sec - delta)
            logger.info(f"Cooldown active for employee {employee.id}: {wait_left}s remaining")
            return {
                "employee_id": employee.id,
                "message": f"cooldown_wait_{wait_left}s",
            }

    # Авто-определение направления
    if last and (last.direction or "").upper().strip() == "IN":
        direction = "OUT"
    else:
        direction = "IN"

    ev = Event(
        employee_id=employee.id,
        terminal_id=terminal_id,
        direction=direction,
        ts=ts_utc,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    logger.info(f"Terminal scan event created: id={ev.id}, direction={direction}")

    return {
        "employee_id": employee.id,
        "event_id": ev.id,
        "direction": direction,
        "message": f"Registered {direction} for {employee.full_name}",
    }
