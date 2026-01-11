from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import event as event_crud
from app.core.time import to_warsaw, local_date_str
from app.schemas.stats import EmployeeDailyStats, DailyWorkStat


from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_admin

router = APIRouter(
    prefix="/stats",
    dependencies=[Depends(require_admin)]
)





@router.get("/employee/{employee_id}")
def employee_stats(employee_id: int, db: Session = Depends(get_db)):
    events = event_crud.list_events_for_employee(db, employee_id)
    if not events:
        raise HTTPException(status_code=404, detail="No events for employee")

    total_seconds = 0
    intervals = []

    open_in: datetime | None = None

    for ev in events:
        d = ev.direction.upper()
        if d == "IN":
            open_in = ev.ts
        elif d == "OUT":
            if open_in is not None and ev.ts >= open_in:
                dur = (ev.ts - open_in).total_seconds()
                total_seconds += dur

                intervals.append(
                    {
                        "in_utc": open_in.isoformat(),
                        "out_utc": ev.ts.isoformat(),
                        "in_local": to_warsaw(open_in).isoformat(),
                        "out_local": to_warsaw(ev.ts).isoformat(),
                        "minutes": int(dur // 60),
                    }
                )
                open_in = None

    return {
        "employee_id": employee_id,
        "total_minutes": int(total_seconds // 60),
        "intervals": intervals,
        "events": [
            {
                "id": ev.id,
                "direction": ev.direction,
                "ts_utc": ev.ts.isoformat(),
                "ts_local": to_warsaw(ev.ts).isoformat(),
                "terminal_id": ev.terminal_id,
            }
            for ev in events
        ],
    }


@router.get("/employee/{employee_id}/daily", response_model=EmployeeDailyStats)
def employee_daily_stats(
    employee_id: int,
    db: Session = Depends(get_db),
    from_date: date = Query(..., description="YYYY-MM-DD (local Europe/Warsaw date)"),
    to_date: date = Query(..., description="YYYY-MM-DD (local Europe/Warsaw date)"),
):
    events = event_crud.list_events_for_employee(db, employee_id)
    if not events:
        raise HTTPException(status_code=404, detail="No events for employee")

    daily: dict[str, dict] = {}

    open_in: datetime | None = None
    for ev in events:
        d = ev.direction.upper()
        if d == "IN":
            open_in = ev.ts
        elif d == "OUT" and open_in is not None and ev.ts >= open_in:
            in_utc = open_in
            out_utc = ev.ts
            open_in = None

            # MVP: относим интервал к дню локального IN (Warsaw)
            day_key = local_date_str(in_utc)

            if day_key not in daily:
                daily[day_key] = {
                    "worked_seconds": 0,
                    "first_in": in_utc,
                    "last_out": out_utc,
                }

            daily[day_key]["worked_seconds"] += (out_utc - in_utc).total_seconds()

            if in_utc < daily[day_key]["first_in"]:
                daily[day_key]["first_in"] = in_utc
            if out_utc > daily[day_key]["last_out"]:
                daily[day_key]["last_out"] = out_utc

    # Заполняем дни в диапазоне, даже если 0 минут
    items: list[DailyWorkStat] = []
    cur = from_date
    while cur <= to_date:
        key = cur.isoformat()
        if key in daily:
            first_in = daily[key]["first_in"]
            last_out = daily[key]["last_out"]
            items.append(
                DailyWorkStat(
                    date_local=key,
                    worked_minutes=int(daily[key]["worked_seconds"] // 60),
                    first_in_local=to_warsaw(first_in).isoformat(),
                    last_out_local=to_warsaw(last_out).isoformat(),
                )
            )
        else:
            items.append(DailyWorkStat(date_local=key, worked_minutes=0))
        cur = date.fromordinal(cur.toordinal() + 1)

    return EmployeeDailyStats(
        employee_id=employee_id,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        items=items,
    )
