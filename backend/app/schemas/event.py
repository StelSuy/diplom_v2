from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EventCreate(BaseModel):
    employee_id: int
    terminal_id: int
    direction: str  # IN/OUT
    ts: datetime


class EventOut(BaseModel):
    id: int
    employee_id: int
    terminal_id: int
    direction: str
    ts: datetime

    class Config:
        from_attributes = True


# ВИПРАВЛЕНО: вилучено дублюючий імпорт BaseModel/datetime.
# terminal_name залишений як Optional — термінал береться з X-Terminal-Key,
# але поле можна передати для логів (не використовується в логіці).
# ts: якщо None — ensure_utc() підставить now(UTC), що є очікуваною поведінкою.
class NFCEventCreate(BaseModel):
    terminal_name: Optional[str] = None  # ігнорується — термінал з X-Terminal-Key
    nfc_uid: str
    direction: str  # "IN" | "OUT"
    ts: Optional[datetime] = None        # None → server time (UTC)
