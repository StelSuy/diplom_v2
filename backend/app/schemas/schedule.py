
from datetime import date
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    employee_id: int
    planned_minutes: int = 0


class ScheduleOut(BaseModel):
    id: int
    employee_id: int
    planned_minutes: int

    class Config:
        from_attributes = True




class ScheduleCell(BaseModel):
    employee_id: int
    day: date
    start_hhmm: str | None = None
    end_hhmm: str | None = None
    code: str | None = None


class ScheduleCellUpsert(BaseModel):
    employee_id: int
    day: date
    start_hhmm: str | None = None
    end_hhmm: str | None = None
    code: str | None = None


class ScheduleRangeResponse(BaseModel):
    date_from: date
    date_to: date
    items: list[ScheduleCell]
