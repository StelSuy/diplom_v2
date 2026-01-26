from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class EventCreate(BaseModel):
    employee_id: int
    terminal_id: int
    direction: str  # IN/OUT
    ts: datetime


class EventOut(BaseModel):
    id: int
    employee_id: int
    terminal_id: Optional[int]
    direction: str
    ts: datetime
    is_manual: bool = False
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class NFCEventCreate(BaseModel):
    terminal_name: str
    nfc_uid: str
    direction: str  # "IN" | "OUT"
    ts: datetime | None = None


class ManualEventCreate(BaseModel):
    employee_id: int = Field(..., gt=0, description="ID співробітника")
    timestamp: str = Field(..., description="ISO timestamp у форматі YYYY-MM-DDTHH:MM:SS")
    direction: str = Field(..., description="IN або OUT")
    terminal_id: Optional[int] = Field(None, gt=0, description="ID терміналу (опціонально)")
    comment: str = Field(..., min_length=1, max_length=500, description="Коментар до події")
    
    @validator('direction')
    def validate_direction(cls, v):
        v = v.upper().strip()
        if v not in ['IN', 'OUT']:
            raise ValueError('direction має бути IN або OUT')
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Невірний формат timestamp (очікується ISO: YYYY-MM-DDTHH:MM:SS)')
