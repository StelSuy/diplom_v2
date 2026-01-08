from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, timezone

from app.core.time import ensure_utc
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
    direction = direction.upper().strip()
    if direction not in ("IN", "OUT"):
        raise ValueError("direction must be IN or OUT")

    last = get_last_event_for_employee(db, employee_id)

    if last and last.direction.upper() == direction:
        raise ValueError(f"Duplicate direction: last was {last.direction}")

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


# =========================
# FIXED: Terminal secure scan
# =========================
def create_event_from_terminal_scan(db: Session, payload: TerminalScanRequest) -> dict:
    uid = payload.uid.strip().upper()
    direction = payload.direction.strip().upper()
    terminal_id = str(payload.terminal_id).strip()

    employee = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if not employee:
        raise ValueError("Unknown UID (employee not registered)")

    # защита от IN -> IN / OUT -> OUT
    last = (
        db.query(Event)
        .filter(Event.employee_id == employee.id)
        .order_by(desc(Event.ts))
        .first()
    )

    if last and last.direction.upper() == direction:
        raise ValueError(f"Duplicate direction: previous event is already {direction}")

    # 🔴 ГЛАВНЫЙ ФИКС:
    # payload.ts приходит в миллисекундах → конвертируем в datetime
    ts_ms = int(payload.ts)
    ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

    ts_utc = ensure_utc(ts_dt)

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
