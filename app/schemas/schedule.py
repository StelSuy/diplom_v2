from datetime import date
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """Створення нового графіку"""
    employee_id: int
    planned_minutes: int = 0


class ScheduleOut(BaseModel):
    """Вихідні дані графіку"""
    id: int
    employee_id: int
    planned_minutes: int

    class Config:
        from_attributes = True


class ScheduleCell(BaseModel):
    """Комірка графіку"""
    employee_id: int
    day: date
    start_hhmm: str | None = None
    end_hhmm: str | None = None
    code: str | None = None


class ScheduleCellUpsert(BaseModel):
    """Створення/оновлення комірки графіку"""
    employee_id: int
    day: date
    start_hhmm: str | None = None
    end_hhmm: str | None = None
    code: str | None = None


class ScheduleMonthRequest(BaseModel):
    """Запит графіку за місяць"""
    year: int = Field(..., description="Рік (наприклад: 2026)")
    month: int = Field(..., ge=1, le=12, description="Місяць (1-12)")
    employee_id: int | None = Field(default=None, description="ID працівника (опціонально)")


class ScheduleRangeResponse(BaseModel):
    """Відповідь з графіком за період"""
    date_from: date
    date_to: date
    items: list[ScheduleCell]


class ScheduleBatchUpsert(BaseModel):
    """Масове збереження комірок графіку"""
    cells: list[ScheduleCellUpsert] = Field(default_factory=list)


class ScheduleBatchResponse(BaseModel):
    """Результат масового збереження"""
    success: int = 0  # кількість успішно збережених
    failed: int = 0   # кількість з помилками
    errors: list[dict] = Field(default_factory=list)  # деталі помилок
