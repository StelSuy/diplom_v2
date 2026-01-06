from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)

    # РџСЂРёРјРµСЂ: РїР»Р°РЅ РІ РјРёРЅСѓС‚Р°С… РЅР° РґРµРЅСЊ/РЅРµРґРµР»СЋ (РїРѕС‚РѕРј СѓС‚РѕС‡РЅРёРј РјРѕРґРµР»СЊ)
    planned_minutes: Mapped[int] = mapped_column(Integer, default=0)
