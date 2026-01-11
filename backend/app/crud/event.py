from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, timezone

from app.core.time import ensure_utc
from app.core.config import settings
from app.models.event import Event
from app.models.employee import Employee
from app.schemas.terminal import TerminalScanRequest


def get_last_event_for_employee(db: Session, employee_id: int) -> Event | None:
    return (
        db.query(Event)
        .filter(Event.employee_id == employee_id)
        .order_by(desc(Event.ts))
        .first()
    )


def create_event(
    db: Session,
    employee_id: int,
    terminal_id: int | str,
    direction: str,
    ts,
) -> Event:
    """
    Базовое создание события.
    Здесь без проверки на дубль направления — т.к. направление может определяться выше.
    """
    direction = direction.upper().strip()
    if direction not in ("IN", "OUT"):
        raise ValueError("direction must be IN or OUT")

    ts_utc = ensure_utc(ts)

    ev = Event(
        employee_id=employee_id,
        terminal_id=str(terminal_id),
        direction=direction,
        ts=ts_utc,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_events_for_employee(db: Session, employee_id: int) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.employee_id == employee_id)
        .order_by(asc(Event.ts))
        .all()
    )


def create_event_from_terminal_scan(db: Session, payload: TerminalScanRequest) -> dict:
    """
    ВАЖНО: сервер сам определяет направление:
      - если последнее событие IN -> новое OUT
      - иначе -> новое IN

    payload.direction принимаем, но НЕ доверяем (для стабильности, пока Android шлёт IN всегда).
    payload.ts ожидается в миллисекундах (Android).
    """

    uid = payload.uid.strip().upper()
    terminal_id = str(payload.terminal_id).strip()

    employee = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if not employee:
        raise ValueError("Unknown UID (employee not registered)")

    # ts из Android: миллисекунды -> datetime UTC
    ts_ms = int(payload.ts)
    ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    ts_utc = ensure_utc(ts_dt)

    last = get_last_event_for_employee(db, employee.id)

    # Cooldown (если задан в Settings / .env)
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
            # Важно: НЕ кидаем 400, иначе Android может уходить в fallback first-scan.
            return {
                "employee_id": employee.id,
                "message": f"cooldown_wait_{wait_left}s",
            }

    # Авто-направление
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

    return {
        "employee_id": employee.id,
        "message": f"Registered {direction} for {employee.full_name}",
    }
