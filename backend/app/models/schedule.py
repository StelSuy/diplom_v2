from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    day = Column(Date, nullable=False, index=True)
    start_hhmm = Column(String(5), nullable=False)
    end_hhmm = Column(String(5), nullable=False)
    code = Column(String(32), nullable=True)

    employee = relationship("Employee")

    __table_args__ = (
        UniqueConstraint("employee_id", "day", name="uq_schedule_employee_day"),
    )
