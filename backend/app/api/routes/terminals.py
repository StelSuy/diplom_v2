import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import terminal as terminal_crud

from app.schemas.terminal import (
    TerminalRegisterRequest,
    TerminalRegisterResponse,
    TerminalScanRequest,
    TerminalScanResponse,
    TerminalSecureScanRequest,
    TerminalSecureScanResponse,
)

from app.crud.employee import create_employee_from_terminal_registration
from app.crud.event import create_event_from_terminal_scan

from app.security.verify import verify_signature
from app.crud import employee as employee_crud
from app.models.event import Event
from app.models.terminal import Terminal  # <-- ДОДАНО: для перевірки існування терміналу

log = logging.getLogger("uvicorn.error")


# =========================
# Helpers (без зміни CRUD)
# =========================
def _require_terminal_registered(db: Session, terminal_id: int) -> Terminal:
    """
    Якщо terminal_id не існує -> 400 "Terminal not registered"
    Це прибирає 500 від FK/IntegrityError і робить демо стабільним.
    """
    term = db.get(Terminal, terminal_id)
    if term is None:
        raise HTTPException(status_code=400, detail="Terminal not registered")
    return term


# =========================
# Admin-only router
# =========================
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/")
def list_terminals(db: Session = Depends(get_db)):
    """Get list of all terminals"""
    terminals = db.query(Terminal).all()
    return [
        {"id": t.id, "name": t.name, "api_key": t.api_key}
        for t in terminals
    ]


@router.post("/")
def create_terminal(name: str, db: Session = Depends(get_db)):
    existing = terminal_crud.get_by_name(db, name)
    if existing:
        return {"id": existing.id, "name": existing.name, "api_key": existing.api_key}

    term = terminal_crud.create_terminal(db, name=name)
    return {"id": term.id, "name": term.name, "api_key": term.api_key}


@router.post("/{terminal_id}/rotate_key")
def rotate_key(terminal_id: int, db: Session = Depends(get_db)):
    term = terminal_crud.rotate_api_key(db, terminal_id)
    if not term:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return {"id": term.id, "name": term.name, "api_key": term.api_key}


# =========================
# Public router for Android terminal app
# (NO require_admin)
# prefix will be set in api/router.py
# =========================
router_public = APIRouter()


@router_public.post("/register", response_model=TerminalRegisterResponse)
def terminal_register(payload: TerminalRegisterRequest, db: Session = Depends(get_db)):
    """
    Android Registration:
    - scan UID (tag)
    - send {uid, code, first_name, last_name, created_by_terminal_id}

    ДОДАНО:
    - якщо created_by_terminal_id не існує -> 400 "Terminal not registered"
    - ловимо IntegrityError -> 400 замість 500
    """
    # Якщо у схемі поле може називатись інакше — підправ тут
    terminal_id = getattr(payload, "created_by_terminal_id", None)
    if terminal_id is not None:
        _require_terminal_registered(db, int(terminal_id))

    try:
        employee = create_employee_from_terminal_registration(db=db, payload=payload)
        return TerminalRegisterResponse(
            ok=True,
            message="Employee registered",
            employee_id=employee.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        # Напр. FK на термінал/унікальності/тощо — не даємо 500
        db.rollback()
        raise HTTPException(status_code=400, detail="Terminal not registered")


@router_public.post("/scan", response_model=TerminalScanResponse)
def terminal_scan(payload: TerminalScanRequest, db: Session = Depends(get_db)):
    """
    Android Scan (non-secure):
    - send {uid, terminal_id, direction, ts}
    NOTE: direction может игнорироваться на сервере (см. crud/event.py)

    ДОДАНО:
    - terminal_id має існувати -> інакше 400 "Terminal not registered"
    - ловимо IntegrityError -> 400 замість 500
    """
    _require_terminal_registered(db, payload.terminal_id)

    try:
        result = create_event_from_terminal_scan(db=db, payload=payload)
        return TerminalScanResponse(
            ok=True,
            message=result["message"],
            employee_id=result["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Terminal not registered")


# =========================
# SECURE SCAN (Challenge–Response)
# =========================
@router_public.post("/secure-scan", response_model=TerminalSecureScanResponse)
def terminal_secure_scan(payload: TerminalSecureScanRequest, db: Session = Depends(get_db)):
    """
    Android Secure Scan:
    - terminal reads employee_uid via HCE
    - terminal generates challenge and gets signature from employee
    - terminal sends {employee_uid, terminal_id, direction, ts, challenge_b64, signature_b64}
    - backend verifies signature using employee.public_key_b64
    - then creates event (direction is determined server-side)

    ДОДАНО:
    - terminal_id має існувати -> 400 "Terminal not registered"
    - ловимо IntegrityError -> 400 замість 500
    """
    log.error(
        f"SECURE_SCAN payload employee_uid={payload.employee_uid} "
        f"direction={payload.direction} terminal_id={payload.terminal_id} ts={payload.ts}"
    )

    # 0) Перевірка терміналу (щоб не було 500 по FK)
    _require_terminal_registered(db, payload.terminal_id)

    # 1) найти сотрудника по employee_uid
    employee = employee_crud.get_by_uid(db, uid=payload.employee_uid)
    if not employee:
        log.info("SECURE_SCAN employee not found")
        raise HTTPException(status_code=404, detail="Employee not found")

    if not getattr(employee, "public_key_b64", None):
        log.info("SECURE_SCAN employee has no public key")
        raise HTTPException(status_code=400, detail="Employee has no public key registered")

    # 2) проверить подпись
    ok = verify_signature(
        public_key_b64=employee.public_key_b64,
        challenge_b64=payload.challenge_b64,
        signature_b64=payload.signature_b64,
    )
    if not ok:
        log.error("SECURE_SCAN bad_signature")
        # 200, но ok=false — Android должен обработать как отказ
        return TerminalSecureScanResponse(ok=False, message="bad_signature", employee_id=None)

    # 3) подпись ок — создаём событие через общую логику
    try:
        scan_payload = TerminalScanRequest(
            uid=payload.employee_uid,
            terminal_id=payload.terminal_id,
            direction=payload.direction,  # может игнорироваться в CRUD
            ts=payload.ts,
        )
        result = create_event_from_terminal_scan(db=db, payload=scan_payload)

        # Логируем то, что реально записалось в БД (последнее событие)
        last = (
            db.query(Event)
            .filter(Event.employee_id == result["employee_id"])
            .order_by(desc(Event.ts))
            .first()
        )
        if last:
            log.error(f"SECURE_SCAN saved direction={last.direction} ts={last.ts}")

        return TerminalSecureScanResponse(
            ok=True,
            message=result["message"],
            employee_id=result["employee_id"],
        )
    except ValueError as e:
        log.error(f"SECURE_SCAN 400: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Terminal not registered")
