from pydantic import BaseModel


class DailyWorkStat(BaseModel):
    date_local: str  # YYYY-MM-DD in Europe/Warsaw

    worked_minutes: int
    worked_seconds: int | None = None
    worked_hms: str | None = None

    first_in_local: str | None = None
    last_out_local: str | None = None

    # ✅ новое: если есть IN без OUT в этот день
    open_shift: bool | None = None


class EmployeeDailyStats(BaseModel):
    employee_id: int
    from_date: str
    to_date: str
    items: list[DailyWorkStat]
