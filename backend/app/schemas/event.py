from datetime import datetime
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


from pydantic import BaseModel
from datetime import datetime


class NFCEventCreate(BaseModel):
    terminal_name: str
    nfc_uid: str
    direction: str  # "IN" | "OUT"
    ts: datetime | None = None
