from __future__ import annotations

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import event as event_crud
from app.core.time import to_warsaw, local_date_str
from app.schemas.stats import EmployeeDailyStats, DailyWorkStat

router = APIRouter(prefix="/stats", dependencies=[Depends(require_admin)])


def _hms_from_seconds(total_seconds: int) -> str:
    if total_seconds < 0:
        total_seconds = 0
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


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

    # daily[day] = worked_seconds, first_in, last_out, open_shift
    daily: dict[str, dict] = {}

    # open_in_by_day нужен, чтобы отметить день как open_shift
    open_in: datetime | None = None
    open_in_day_key: str | None = None

    for ev in events:
        d = ev.direction.upper()

        if d == "IN":
            open_in = ev.ts
            open_in_day_key = local_date_str(ev.ts)

            if open_in_day_key not in daily:
                daily[open_in_day_key] = {
                    "worked_seconds": 0,
                    "first_in": ev.ts,
                    "last_out": None,
                    "open_shift": True,
                }
            else:
                if ev.ts < daily[open_in_day_key]["first_in"]:
                    daily[open_in_day_key]["first_in"] = ev.ts
                daily[open_in_day_key]["open_shift"] = True

        elif d == "OUT":
            if open_in is not None and ev.ts >= open_in:
                in_utc = open_in
                out_utc = ev.ts
                day_key = local_date_str(in_utc)

                if day_key not in daily:
                    daily[day_key] = {
                        "worked_seconds": 0,
                        "first_in": in_utc,
                        "last_out": None,
                        "open_shift": False,
                    }

                daily[day_key]["worked_seconds"] += int((out_utc - in_utc).total_seconds())

                # last_out обновляем только реальным OUT
                if daily[day_key]["last_out"] is None or out_utc > daily[day_key]["last_out"]:
                    daily[day_key]["last_out"] = out_utc

                # интервал закрыт
                daily[day_key]["open_shift"] = False

                open_in = None
                open_in_day_key = None

    # если цикл закончился, и open_in не закрыт — open_shift уже True в daily[day]
    items: list[DailyWorkStat] = []
    cur = from_date
    while cur <= to_date:
        key = cur.isoformat()

        if key in daily:
            first_in = daily[key].get("first_in")
            last_out = daily[key].get("last_out")
            open_shift = bool(daily[key].get("open_shift", False))

            worked_seconds = int(daily[key].get("worked_seconds", 0))
            worked_hms = _hms_from_seconds(worked_seconds)
            worked_minutes = worked_seconds // 60

            items.append(
                DailyWorkStat(
                    date_local=key,
                    worked_minutes=int(worked_minutes),
                    worked_seconds=worked_seconds,
                    worked_hms=worked_hms,
                    first_in_local=to_warsaw(first_in).isoformat() if first_in else None,
                    # ✅ если open_shift=True → показываем Last OUT пустым
                    last_out_local=None if open_shift else (to_warsaw(last_out).isoformat() if last_out else None),
                    open_shift=open_shift,
                )
            )
        else:
            items.append(DailyWorkStat(date_local=key, worked_minutes=0, worked_seconds=0, worked_hms="00:00:00", open_shift=False))

        cur = date.fromordinal(cur.toordinal() + 1)

    return EmployeeDailyStats(
        employee_id=employee_id,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        items=items,
    )
