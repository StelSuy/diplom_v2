from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import NFCEventCreate
from app.crud import employee as employee_crud
from app.crud import terminal as terminal_crud
from app.crud import event as event_crud
from app.api.deps import get_current_terminal
from app.models.terminal import Terminal


router = APIRouter()


@router.post("/nfc")
def create_nfc_event(
    payload: NFCEventCreate,
    terminal: Terminal = Depends(get_current_terminal),
    db: Session = Depends(get_db),
):
    # Employee by uid
    emp = employee_crud.get_by_uid(db, payload.nfc_uid)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found by nfc_uid")

    # Терминал берём из ключа (не доверяем terminal_name из payload)
    # Но можем проверить/обновить имя (необязательно). MVP: если не совпало — игнорируем payload.name.
    term = terminal

    try:
        ev = event_crud.create_event(
            db=db,
            employee_id=emp.id,
            terminal_id=term.id,
            direction=payload.direction,
            ts=payload.ts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "ok": True,
        "event": {
            "id": ev.id,
            "employee_id": ev.employee_id,
            "terminal_id": ev.terminal_id,
            "direction": ev.direction,
            "ts": ev.ts.isoformat(),
        },
        "employee": {"id": emp.id, "full_name": emp.full_name},
        "terminal": {"id": term.id, "name": term.name},
    }
