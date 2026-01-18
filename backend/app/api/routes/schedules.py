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


def _time_cell(start_hhmm: str | None, end_hhmm: str | None, code: str | None, cell_h: float):
    """
    Рендерит содержимое ячейки:
    - если есть code -> показываем code по центру
    - иначе: сверху start_hhmm (приход), снизу end_hhmm (уход)
    """
    if code:
        # Однострочно, по центру
        t = Table([[code]], rowHeights=[cell_h], colWidths=None)
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
            ("BOX", (0, 0), (-1, -1), 0, colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ]))
        return t

    top = start_hhmm or ""
    bottom = end_hhmm or ""

    # 2 строки внутри одной ячейки
    t = Table(
        [[top], [bottom]],
        rowHeights=[cell_h / 2.0, cell_h / 2.0],
        colWidths=None,
    )
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),

        # чтобы выглядело как одна ячейка — без внутренних рамок
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),

        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


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

    # индексируем по (employee_id, day) -> (start, end, code)
    idx: dict[tuple[int, date], tuple[str | None, str | None, str | None]] = {}
    for r in rows:
        idx[(r.employee_id, r.day)] = (r.start_hhmm, r.end_hhmm, r.code)

    days = list(_daterange(date_from, date_to))

    header = ["№", "ПІБ", "Посада"] + [d.strftime("%d") for d in days]
    data: list[list[object]] = [header]

    # высота строки (подбирай)
    CELL_H = 18

    for i, e in enumerate(employees, start=1):
        row: list[object] = [str(i), e.full_name, (e.position or "")]
        for d in days:
            start_hhmm, end_hhmm, code = idx.get((e.id, d), (None, None, None))
            row.append(_time_cell(start_hhmm, end_hhmm, code, CELL_H))
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

    # фиксируем высоты строк, чтобы не было "криво"
    row_heights = [CELL_H] * len(data)
    tbl = Table(data, repeatRows=1, rowHeights=row_heights)

    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),

        # Паддинги чуть поменьше, чтоб влезало
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
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
