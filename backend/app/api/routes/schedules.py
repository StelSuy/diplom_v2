from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import schedule as schedule_crud
from app.crud import employee as employee_crud
from app.schemas.schedule import ScheduleCellUpsert, ScheduleRangeResponse, ScheduleCell

router = APIRouter(prefix="/schedule", dependencies=[Depends(require_admin)], tags=["schedule"])


def _daterange(d1: date, d2: date):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)


def _cell_text(start_hhmm: str | None, end_hhmm: str | None, code: str | None) -> str:
    if code:
        return code
    if start_hhmm and end_hhmm:
        return f"{start_hhmm}-{end_hhmm}"
    if start_hhmm and not end_hhmm:
        return f"{start_hhmm}-"
    if end_hhmm and not start_hhmm:
        return f"-{end_hhmm}"
    return ""


@router.get("", response_model=ScheduleRangeResponse)
def get_schedule(
    date_from: date = Query(...),
    date_to: date = Query(...),
    employee_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    rows = schedule_crud.get_range(db, date_from=date_from, date_to=date_to, employee_id=employee_id)
    items = [
        ScheduleCell(
            employee_id=r.employee_id,
            day=r.day,
            start_hhmm=r.start_hhmm,
            end_hhmm=r.end_hhmm,
            code=r.code,
        )
        for r in rows
    ]
    return ScheduleRangeResponse(date_from=date_from, date_to=date_to, items=items)


@router.post("/cell", response_model=ScheduleCell)
def upsert_schedule_cell(payload: ScheduleCellUpsert, db: Session = Depends(get_db)):
    row = schedule_crud.upsert_cell(
        db=db,
        employee_id=payload.employee_id,
        day=payload.day,
        start_hhmm=payload.start_hhmm,
        end_hhmm=payload.end_hhmm,
        code=payload.code,
    )
    return ScheduleCell(
        employee_id=row.employee_id,
        day=row.day,
        start_hhmm=row.start_hhmm,
        end_hhmm=row.end_hhmm,
        code=row.code,
    )


@router.get("/pdf")
def schedule_pdf(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
):
    employees = employee_crud.get_all(db)
    rows = schedule_crud.get_range(db, date_from=date_from, date_to=date_to, employee_id=None)

    idx: dict[tuple[int, date], str] = {}
    for r in rows:
        idx[(r.employee_id, r.day)] = _cell_text(r.start_hhmm, r.end_hhmm, r.code)

    days = list(_daterange(date_from, date_to))

    header = ["№", "ПІБ", "Посада"] + [d.strftime("%d") for d in days]
    data = [header]

    for i, e in enumerate(employees, start=1):
        row = [str(i), e.full_name, (e.position or "")]
        for d in days:
            row.append(idx.get((e.id, d), ""))
        data.append(row)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=12,
        rightMargin=12,
        topMargin=12,
        bottomMargin=12,
        title="Schedule",
    )

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Графік змін: {date_from.isoformat()} — {date_to.isoformat()}", styles["Title"]))
    story.append(Spacer(1, 8))

    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(tbl)
    doc.build(story)

    buf.seek(0)
    filename = f"schedule_{date_from.isoformat()}_{date_to.isoformat()}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )
