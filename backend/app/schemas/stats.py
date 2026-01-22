from __future__ import annotations

from pydantic import BaseModel


class WorktimeAnomaly(BaseModel):
    code: str
    ts_utc: str | None = None
    ts_local: str | None = None
    details: str | None = None


class DailyWorkStat(BaseModel):
    date_local: str  # YYYY-MM-DD in Europe/Warsaw

    worked_minutes: int
    worked_seconds: int | None = None
    worked_hms: str | None = None

    first_in_local: str | None = None
    last_out_local: str | None = None

    # ✅ якщо є незакрита зміна (IN без OUT) в цей день
    open_shift: bool | None = None

    # ✅ якщо був застосований автоклоуз (для відкритої зміни)
    auto_closed: bool | None = None

    # ✅ аномалії, які стосуються цього дня (може бути порожнім)
    anomalies: list[WorktimeAnomaly] | None = None


class WeekWorkStat(BaseModel):
    week_start_local: str  # YYYY-MM-DD (Mon)
    week_end_local: str    # YYYY-MM-DD (Sun)
    worked_minutes: int
    worked_hms: str


class MonthWorkStat(BaseModel):
    month: str  # YYYY-MM
    worked_minutes: int
    worked_hms: str


class EmployeeDailyStats(BaseModel):
    employee_id: int
    from_date: str
    to_date: str

    # ✅ деталізація по днях
    items: list[DailyWorkStat]

    # ✅ підсумок за діапазон
    total_minutes: int
    total_hms: str

    # ✅ агрегації (для комісії “за тиждень/місяць”)
    weeks: list[WeekWorkStat] | None = None
    months: list[MonthWorkStat] | None = None
