from datetime import datetime, timedelta, time, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

# БАГ №1 ВИПРАВЛЕНО: get_current_user вилучено — require_admin тепер повертає User
from app.api.deps import require_admin
from app.core.time import WARSAW, to_utc
from app.crud import employee as employee_crud
from app.db.session import get_db
from app.models.employee import Employee
from app.models.event import Event
from app.models.user import User

import logging

from app.security.audit import audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events/manual", tags=["manual_events"])


class ManualEventCreate(BaseModel):
    employee_id: int
    timestamp: str  # ISO format: "2026-01-24T14:30:00" (WARSAW LOCAL TIME)
    direction: str  # "IN" or "OUT"
    terminal_id: Optional[int] = None
    comment: str


class ManualEventResponse(BaseModel):
    id: int
    employee_id: int
    employee_full_name: str
    timestamp: str
    ts_local: str
    direction: str
    terminal_id: Optional[int]
    comment: str
    created_by_username: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=dict)
def create_manual_event(
    payload: ManualEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Створити подію вручну (тільки для адміністраторів).
    Можна додавати події за будь-яку дату/час.
    
    ВАЖЛИВО: timestamp приймається як WARSAW LOCAL TIME!
    """
    logger.info("create_manual_event called")
    try:
        # Перевірка співробітника
        employee = employee_crud.get_by_id(db, payload.employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Співробітника не знайдено")

        # Перевірка типу події
        if payload.direction not in ["IN", "OUT"]:
            raise HTTPException(status_code=400, detail="direction має бути 'IN' або 'OUT'")

        # Парсинг timestamp як WARSAW LOCAL TIME
        try:
            # Парсимо як наївний datetime
            dt_naive = datetime.fromisoformat(payload.timestamp)
            
            # Додаємо Warsaw timezone
            dt_warsaw = dt_naive.replace(tzinfo=WARSAW)
            
            # Конвертуємо в UTC для збереження в БД
            dt_utc = to_utc(dt_warsaw)
            
            logger.info(f"Manual event timestamp conversion: local={dt_warsaw.isoformat()} -> utc={dt_utc.isoformat()}")
            
        except ValueError as e:
            logger.error(f"Invalid timestamp format: {payload.timestamp}, error: {e}")
            raise HTTPException(
                status_code=400, 
                detail="Невірний формат timestamp (очікується ISO: YYYY-MM-DDTHH:MM:SS)"
            )

        # БАГ №2 ВИПРАВЛЕНО: datetime.utcnow() замінено на datetime.now(timezone.utc)
        event = Event(
            employee_id=payload.employee_id,
            ts=dt_utc,  # Зберігаємо UTC
            direction=payload.direction,
            terminal_id=payload.terminal_id,
            is_manual=True,
            created_by_user_id=current_user.id,
            comment=payload.comment,
            created_at=datetime.now(timezone.utc),
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            f"Ручна подія створена: ID={event.id}, employee_id={payload.employee_id}, "
            f"ts_utc={dt_utc.isoformat()}, ts_local={dt_warsaw.isoformat()}, "
            f"direction={payload.direction}, admin={current_user.username}"
        )

        audit_log("manual_event_create", current_user.username, details={
            "event_id": event.id, "employee_id": payload.employee_id,
            "direction": payload.direction, "ts_local": dt_warsaw.isoformat(),
        })

        return {
            "id": event.id,
            "employee_id": event.employee_id,
            "timestamp": event.ts.isoformat(),
            "direction": event.direction,
            "created_by": current_user.username,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Помилка створення ручної події")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Не вдалося створити подію: {str(e)}")


@router.get("", response_model=list[dict])
def get_manual_events(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Отримати список ручних подій.
    """
    logger.info("get_manual_events called")
    try:
        events = (
            db.query(Event, Employee, User)
            .join(Employee, Event.employee_id == Employee.id)
            .outerjoin(User, Event.created_by_user_id == User.id)
            .filter(Event.is_manual == True)
            .order_by(Event.ts.desc())
            .limit(limit)
            .all()
        )

        result = []
        for event, employee, user in events:
            # Форматування дати і часу для зручності фронтенду
            ts_datetime = event.ts
            date_str = ts_datetime.strftime("%Y-%m-%d")
            time_str = ts_datetime.strftime("%H:%M:%S")
            datetime_str = ts_datetime.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append({
                "id": event.id,
                "employee_id": event.employee_id,
                "employee_full_name": employee.full_name,
                "timestamp": event.ts.isoformat(),
                "ts_local": datetime_str,
                "date": date_str,
                "time": time_str,
                "direction": event.direction,
                "terminal_id": event.terminal_id,
                "comment": event.comment,
                "created_by_username": user.username if user else "—",
                "created_at": event.created_at.isoformat() if event.created_at else None,
            })

        return result

    except Exception as e:
        logger.exception("Помилка отримання ручних подій")
        raise HTTPException(status_code=500, detail=f"Не вдалося отримати події: {str(e)}")


@router.delete("/{event_id}")
def delete_manual_event(
        event_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin),
):
    """
    Видалити ручну подію (тільки для адміністраторів).
    """
    logger.info(f"delete_manual_event called for event_id={event_id}")

    try:
        # Перевірка що подія існує
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Подію не знайдено")

        # Перевірка що це ручна подія
        if not event.is_manual:
            raise HTTPException(
                status_code=400,
                detail="Можна видаляти тільки ручні події"
            )

        # Видалення
        db.delete(event)
        db.commit()

        logger.info(
            f"Ручна подія видалена: ID={event_id}, "
            f"employee_id={event.employee_id}, admin={current_user.username}"
        )

        audit_log("manual_event_delete", current_user.username, details={
            "event_id": event_id, "employee_id": event.employee_id,
        })

        return {"success": True, "deleted_id": event_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Помилка видалення ручної події")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Не вдалося видалити подію: {str(e)}")


@router.delete("/day/{employee_id}/{date}")
def delete_events_for_day(
        employee_id: int,
        date: str,  # YYYY-MM-DD
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin),
):
    """
    Видалити ВСІ події співробітника за конкретну дату (Europe/Warsaw).
    Використовується для очистки статистики за день.
    """
    logger.info(f"delete_events_for_day: employee_id={employee_id}, date={date}, admin={current_user.username}")

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        start_warsaw = datetime.combine(date_obj, time.min).replace(tzinfo=WARSAW)
        end_warsaw = start_warsaw + timedelta(days=1)
        start_utc = to_utc(start_warsaw).replace(tzinfo=None)
        end_utc = to_utc(end_warsaw).replace(tzinfo=None)

        events = (
            db.query(Event)
            .filter(Event.employee_id == employee_id)
            .filter(Event.ts >= start_utc)
            .filter(Event.ts < end_utc)
            .all()
        )

        count = len(events)
        for ev in events:
            db.delete(ev)
        db.commit()

        logger.info(
            f"Видалено {count} подій за {date} для employee_id={employee_id}, "
            f"admin={current_user.username}"
        )

        audit_log("clear_day_events", current_user.username, details={
            "employee_id": employee_id, "date": date, "deleted_count": count,
        })

        return {"success": True, "deleted_count": count, "date": date, "employee_id": employee_id}

    except ValueError:
        raise HTTPException(status_code=400, detail="Невірний формат дати (очікується YYYY-MM-DD)")
    except Exception as e:
        logger.exception("Помилка видалення подій за день")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Помилка: {str(e)}")


@router.get("/date/{employee_id}/{date}")
def get_events_for_date(
        employee_id: int,
        date: str,  # YYYY-MM-DD (локальна дата Europe/Warsaw)
        db: Session = Depends(get_db),
        _: User = Depends(require_admin),
):
    """
    Отримати всі ручні події для співробітника на конкретну дату (Europe/Warsaw).
    """
    logger.info(f"get_events_for_date called: employee_id={employee_id}, date={date}")

    try:

        # Парсимо дату
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Діапазон доби в WARSAW (00:00..00:00 наступного дня)
        start_warsaw = datetime.combine(date_obj, time.min).replace(tzinfo=WARSAW)
        end_warsaw = start_warsaw + timedelta(days=1)

        # Переводимо в UTC (і робимо naive, бо в моделі DateTime без timezone)
        start_utc = to_utc(start_warsaw).replace(tzinfo=None)
        end_utc = to_utc(end_warsaw).replace(tzinfo=None)

        events = (
            db.query(Event)
            .filter(Event.employee_id == employee_id)
            .filter(Event.is_manual == True)
            .filter(Event.ts >= start_utc)
            .filter(Event.ts < end_utc)
            .order_by(Event.ts.asc())
            .all()
        )

        result = [
            {
                "id": e.id,
                "direction": e.direction,
                "ts": e.ts.isoformat(),
                "comment": e.comment,
            }
            for e in events
        ]

        return {"events": result, "count": len(result)}

    except ValueError:
        raise HTTPException(status_code=400, detail="Невірний формат дати (очікується YYYY-MM-DD)")
    except Exception as e:
        logger.exception("Помилка отримання подій")
        raise HTTPException(status_code=500, detail=f"Помилка: {str(e)}")








