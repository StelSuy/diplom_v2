from pydantic import BaseModel


class DailyWorkStat(BaseModel):
    date_local: str  # YYYY-MM-DD in Europe/Warsaw
    worked_minutes: int
    first_in_local: str | None = None
    last_out_local: str | None = None


class EmployeeDailyStats(BaseModel):
    employee_id: int
    from_date: str
    to_date: str
    items: list[DailyWorkStat]
