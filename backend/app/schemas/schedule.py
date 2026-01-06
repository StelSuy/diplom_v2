from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    employee_id: int
    planned_minutes: int = 0


class ScheduleOut(BaseModel):
    id: int
    employee_id: int
    planned_minutes: int

    class Config:
        from_attributes = True
