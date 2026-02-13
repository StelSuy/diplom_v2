import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.employee import Employee
from app.security.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(check_rate_limit)])


class FirstScanRequest(BaseModel):
    employee_uid: str
    terminal_id: str
    public_key_b64: str


class FirstScanResponse(BaseModel):
    ok: bool
    status: str
    employee_id: int | None = None


@router.post("/first-scan")
def first_scan(payload: FirstScanRequest, db: Session = Depends(get_db)):
    uid = payload.employee_uid.strip().upper()
    logger.info(f"FIRST_SCAN uid={uid}")

    emp = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if not emp:
        sample = db.query(Employee.nfc_uid).limit(10).all()
        logger.warning(f"FIRST_SCAN not found. Sample UIDs in DB: {sample}")
        raise HTTPException(status_code=404, detail="Employee not found")

    # ⬇️ ДОДАТИ ЦЮ ПЕРЕВІРКУ
    if emp.public_key_b64:
        raise HTTPException(status_code=400, detail="Public key already registered. Contact admin to reset.")

    emp.public_key_b64 = payload.public_key_b64.strip()
    db.commit()
    db.refresh(emp)

    return FirstScanResponse(ok=True, status="public_key_saved", employee_id=emp.id)