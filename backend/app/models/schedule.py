from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    day = Column(Date, nullable=False, index=True)

    # MySQL: VARCHAR потребує довжину
    start_hhmm = Column(String(5), nullable=True)   # "07:00"
    end_hhmm = Column(String(5), nullable=True)     # "19:00"
    code = Column(String(32), nullable=True)        # "В", "Відр.", "Лікарн.", etc.

    employee = relationship("Employee")

    __table_args__ = (
        UniqueConstraint("employee_id", "day", name="uq_schedule_employee_day"),
    )
