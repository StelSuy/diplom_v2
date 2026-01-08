from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.employee import Employee

router = APIRouter()


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
    print("FIRST_SCAN uid=", uid)

    emp = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if not emp:
        sample = db.query(Employee.nfc_uid).limit(10).all()
        print("FIRST_SCAN not found. Sample UIDs in DB:", sample)
        raise HTTPException(status_code=404, detail="Employee not found for this UID. Register employee first.")

    emp.public_key_b64 = payload.public_key_b64.strip()
    db.commit()
    db.refresh(emp)

    return FirstScanResponse(ok=True, status="public_key_saved", employee_id=emp.id)
