from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Schedule(Base):
    """Модель графіку роботи працівника"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, comment="ID працівника")
    day = Column(Date, nullable=False, index=True, comment="День")
    start_hhmm = Column(String(5), nullable=False, comment="Час початку (ГГ:ХХ)")
    end_hhmm = Column(String(5), nullable=False, comment="Час закінчення (ГГ:ХХ)")
    code = Column(String(32), nullable=True, comment="Код зміни (В - вихідний, ОФ - офіс)")

    employee = relationship("Employee")

    __table_args__ = (
        UniqueConstraint("employee_id", "day", name="uq_schedule_employee_day"),
    )
