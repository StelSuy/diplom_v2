from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import terminal as terminal_crud

# NEW imports (schemas + crud for scan/register)
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

# SECURITY
from app.security.verify import verify_signature
from app.crud import employee as employee_crud


# =========================
# Admin-only router (as you had)
# =========================
router = APIRouter(dependencies=[Depends(require_admin)])


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
    """
    try:
        employee = create_employee_from_terminal_registration(db=db, payload=payload)
        return TerminalRegisterResponse(
            ok=True,
            message="Employee registered",
            employee_id=employee.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_public.post("/scan", response_model=TerminalScanResponse)
def terminal_scan(payload: TerminalScanRequest, db: Session = Depends(get_db)):
    """
    Android Scan:
    - send {uid, terminal_id, direction, ts}
    """
    try:
        result = create_event_from_terminal_scan(db=db, payload=payload)
        return TerminalScanResponse(
            ok=True,
            message=result["message"],
            employee_id=result["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# SECURE SCAN (Challenge–Response)
# =========================
@router_public.post("/secure-scan")
def terminal_secure_scan(payload: TerminalSecureScanRequest, db: Session = Depends(get_db)):
    """
    Android Secure Scan:
    - terminal reads employee_uid via HCE
    - terminal generates challenge (random bytes) and sends to employee via APDU
    - employee returns signature_b64
    - terminal sends {employee_uid, terminal_id, direction, ts, challenge_b64, signature_b64}
    - backend verifies signature using employee.public_key_b64
    """
    # 1) найти сотрудника по employee_uid
    employee = employee_crud.get_by_uid(db, uid=payload.employee_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not employee.public_key_b64:
        raise HTTPException(status_code=400, detail="Employee has no public key registered")

    # 2) проверить подпись
    ok = verify_signature(
        public_key_b64=employee.public_key_b64,
        challenge_b64=payload.challenge_b64,
        signature_b64=payload.signature_b64,
    )
    if not ok:
        return TerminalSecureScanResponse(ok=False, message="bad_signature", employee_id=None)

    # 3) если подпись ок — создаём событие как обычно
    # Используем ту же бизнес-логику, что и в обычном scan,
    # но передаём дальше уже проверенный employee_uid
    try:
        # Можно переиспользовать create_event_from_terminal_scan,
        # если он принимает uid/terminal_id/direction/ts
        scan_payload = TerminalScanRequest(
            uid=payload.employee_uid,
            terminal_id=payload.terminal_id,
            direction=payload.direction,
            ts=payload.ts,
        )
        result = create_event_from_terminal_scan(db=db, payload=scan_payload)

        return TerminalSecureScanResponse(
            ok=True,
            message=result["message"],
            employee_id=result["employee_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
