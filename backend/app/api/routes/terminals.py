import logging
from datetime import timezone as tz

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_admin, get_current_terminal
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
from app.models.terminal import Terminal
from app.core.time import to_warsaw
from app.ws.manager import ws_manager

log = logging.getLogger("uvicorn.error")


# =========================
# Helpers
# =========================
def _require_terminal_registered(db: Session, terminal_id: int) -> Terminal:
    term = db.get(Terminal, terminal_id)
    if term is None:
        raise HTTPException(status_code=400, detail="Terminal not registered")
    return term


def _build_ws_payload(*, result: dict, employee, terminal, last_event=None) -> dict:
    """Build a WS broadcast payload from scan result."""
    ts_local = None
    if last_event and last_event.ts:
        ts_dt = last_event.ts
        if ts_dt.tzinfo is None:
            ts_dt = ts_dt.replace(tzinfo=tz.utc)
        ts_local = to_warsaw(ts_dt)

    return {
        "type": "new_scan",
        "id": result.get("event_id"),
        "employee_id": result["employee_id"],
        "employee_name": employee.full_name if employee else "",
        "position": (employee.position or "") if employee else "",
        "direction": result.get("direction", ""),
        "ts_local": ts_local.strftime("%H:%M:%S") if ts_local else "",
        "date_local": ts_local.strftime("%Y-%m-%d") if ts_local else "",
        "terminal_id": terminal.id if terminal else None,
        "terminal_name": terminal.name if terminal else "",
        "is_manual": False,
        "comment": "",
    }


# =========================
# Admin-only router
# =========================
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/")
def list_terminals(db: Session = Depends(get_db)):
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
# =========================
router_public = APIRouter(dependencies=[Depends(get_current_terminal)])


@router_public.post("/register", response_model=TerminalRegisterResponse)
def terminal_register(payload: TerminalRegisterRequest, db: Session = Depends(get_db)):
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
        db.rollback()
        raise HTTPException(status_code=400, detail="Terminal not registered")


@router_public.post("/scan", response_model=TerminalScanResponse)
async def terminal_scan(payload: TerminalScanRequest, db: Session = Depends(get_db)):
    _require_terminal_registered(db, payload.terminal_id)

    try:
        result = create_event_from_terminal_scan(db=db, payload=payload)

        # WS broadcast (instant — async)
        if result.get("event_id"):
            emp = employee_crud.get_by_uid(db, uid=payload.uid.strip().upper())
            term = db.get(Terminal, payload.terminal_id)
            last = (
                db.query(Event)
                .filter(Event.employee_id == result["employee_id"])
                .order_by(desc(Event.ts))
                .first()
            )
            await ws_manager.broadcast(
                _build_ws_payload(result=result, employee=emp, terminal=term, last_event=last)
            )

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
async def terminal_secure_scan(payload: TerminalSecureScanRequest, db: Session = Depends(get_db)):
    log.info(
        f"SECURE_SCAN payload employee_uid={payload.employee_uid} "
        f"direction={payload.direction} terminal_id={payload.terminal_id} ts={payload.ts}"
    )

    # 0) Перевірка терміналу
    _require_terminal_registered(db, payload.terminal_id)

    # 1) Знайти співробітника
    employee = employee_crud.get_by_uid(db, uid=payload.employee_uid)
    if not employee:
        log.info("SECURE_SCAN employee not found")
        raise HTTPException(status_code=404, detail="Employee not found")

    if not getattr(employee, "public_key_b64", None):
        log.info("SECURE_SCAN employee has no public key")
        raise HTTPException(status_code=400, detail="Employee has no public key registered")

    # 2) Перевірка підпису
    ok = verify_signature(
        public_key_b64=employee.public_key_b64,
        challenge_b64=payload.challenge_b64,
        signature_b64=payload.signature_b64,
    )
    if not ok:
        log.warning("SECURE_SCAN bad_signature")
        return TerminalSecureScanResponse(ok=False, message="bad_signature", employee_id=None)

    # 3) Створення події
    try:
        scan_payload = TerminalScanRequest(
            uid=payload.employee_uid,
            terminal_id=payload.terminal_id,
            direction=payload.direction,
            ts=payload.ts,
        )
        result = create_event_from_terminal_scan(db=db, payload=scan_payload)

        # Останній запис у БД
        last = (
            db.query(Event)
            .filter(Event.employee_id == result["employee_id"])
            .order_by(desc(Event.ts))
            .first()
        )
        if last:
            log.info(f"SECURE_SCAN saved direction={last.direction} ts={last.ts}")

        # WS broadcast (instant — async, await)
        if result.get("event_id"):
            term = db.get(Terminal, payload.terminal_id)
            await ws_manager.broadcast(
                _build_ws_payload(result=result, employee=employee, terminal=term, last_event=last)
            )

        return TerminalSecureScanResponse(
            ok=True,
            message=result["message"],
            employee_id=result["employee_id"],
        )
    except ValueError as e:
        log.warning(f"SECURE_SCAN 400: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Terminal not registered")
