from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.time import ensure_utc
from app.models.event import Event


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
    terminal_id: int,
    direction: str,
    ts,
) -> Event:
    direction = direction.upper().strip()
    if direction not in ("IN", "OUT"):
        raise ValueError("direction must be IN or OUT")

    last = get_last_event_for_employee(db, employee_id)

    # Простейшая валидация: нельзя два раза подряд IN или OUT
    if last and last.direction.upper() == direction:
        raise ValueError(f"Duplicate direction: last was {last.direction}")

    # Нормализация времени: всё в UTC
    ts_utc = ensure_utc(ts)

    ev = Event(employee_id=employee_id, terminal_id=terminal_id, direction=direction, ts=ts_utc)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev



from sqlalchemy import asc

def list_events_for_employee(db: Session, employee_id: int) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.employee_id == employee_id)
        .order_by(asc(Event.ts))
        .all()
    )
