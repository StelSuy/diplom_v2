from __future__ import annotations

from datetime import date, timedelta
from calendar import monthrange
from io import BytesIO
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.platypus.flowables import KeepTogether
from datetime import datetime as dt

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import schedule as schedule_crud
from app.crud import employee as employee_crud
from app.schemas.schedule import (
    ScheduleCellUpsert,
    ScheduleRangeResponse,
    ScheduleCell,
    ScheduleBatchUpsert,
    ScheduleBatchResponse,
    ScheduleMonthRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedule", dependencies=[Depends(require_admin)], tags=["schedule"])


def _daterange(d1: date, d2: date):
    """Генератор діапазону дат"""
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)


def _time_cell(start_hhmm: str | None, end_hhmm: str | None, code: str | None):
    """
    Повертає текст для комірки графіку
    """
    if code and code != "":
        return code

    if start_hhmm == "00:00" and end_hhmm == "00:00":
        return "—"

    if start_hhmm and end_hhmm:
        return f"{start_hhmm}\n{end_hhmm}"

    return "—"


@router.post("/month", response_model=ScheduleRangeResponse)
def get_schedule_by_month(
    payload: ScheduleMonthRequest,
    db: Session = Depends(get_db),
):
    """
    Отримати графік за місяць.
    
    Автоматично створює пусті графіки для працівників, у яких їх немає.
    Якщо вказано employee_id - повертає тільки графік цього працівника.
    Інакше - графіки всіх працівників.
    
    Приклад запиту:
    ```json
    {
      "year": 2026,
      "month": 1,
      "employee_id": 5
    }
    ```
    """
    try:
        # Отримуємо перший і останній день місяця
        _, last_day = monthrange(payload.year, payload.month)
        date_from = date(payload.year, payload.month, 1)
        date_to = date(payload.year, payload.month, last_day)
        
        # Якщо вказано працівника - створюємо пусті графіки тільки для нього
        if payload.employee_id:
            schedule_crud.get_or_create_empty_schedules(
                db, 
                payload.employee_id, 
                payload.year, 
                payload.month
            )
            rows = schedule_crud.get_range(
                db, 
                date_from=date_from, 
                date_to=date_to, 
                employee_id=payload.employee_id
            )
        else:
            # Інакше - для всіх працівників
            schedule_crud.ensure_all_employees_have_schedules(
                db, 
                payload.year, 
                payload.month
            )
            rows = schedule_crud.get_range(
                db, 
                date_from=date_from, 
                date_to=date_to, 
                employee_id=None
            )
        
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
        
    except ValueError as e:
        logger.warning(f"Помилка валідації: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Помилка отримання графіку")
        raise HTTPException(status_code=500, detail=f"Не вдалося отримати графік: {str(e)}")


@router.get("", response_model=ScheduleRangeResponse)
def get_schedule(
    date_from: date = Query(..., description="Дата початку (РРРР-ММ-ДД)"),
    date_to: date = Query(..., description="Дата закінчення (РРРР-ММ-ДД)"),
    employee_id: int | None = Query(default=None, description="Фільтр по ID працівника"),
    db: Session = Depends(get_db),
):
    """
    Отримати графік за період (застарілий метод).
    
    Рекомендується використовувати POST /schedule/month для вибірки за місяцем.
    """
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from має бути <= date_to")
    
    try:
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
    except Exception as e:
        logger.exception("Помилка отримання графіку")
        raise HTTPException(status_code=500, detail=f"Не вдалося отримати графік: {str(e)}")


@router.post("/cell", response_model=ScheduleCell)
def upsert_schedule_cell(payload: ScheduleCellUpsert, db: Session = Depends(get_db)):
    """
    Створити або оновити комірку графіку.
    
    Підтримувані формати:
    1. code + start_hhmm + end_hhmm: явне вказання всіх параметрів
    2. code в форматі "Г-Г" (наприклад "5-7" -> 05:00-07:00)
    3. Пустий code і пусті start/end -> видалення комірки
    
    Приклади:
    - {"employee_id": 1, "day": "2024-01-15", "code": "5-7"} 
    - {"employee_id": 1, "day": "2024-01-15", "start_hhmm": "08:00", "end_hhmm": "17:00", "code": "ОФ"}
    - {"employee_id": 1, "day": "2024-01-15", "code": ""} -> видалення
    """
    logger.info(f"Оновлення комірки графіку: працівник={payload.employee_id}, день={payload.day}, код={payload.code}")
    
    try:
        row = schedule_crud.upsert_cell(
            db=db,
            employee_id=payload.employee_id,
            day=payload.day,
            start_hhmm=payload.start_hhmm,
            end_hhmm=payload.end_hhmm,
            code=payload.code,
        )
        
        logger.info(f"Комірку графіку збережено: id={getattr(row, 'id', None)}, початок={row.start_hhmm}, кінець={row.end_hhmm}")
        
        return ScheduleCell(
            employee_id=row.employee_id,
            day=row.day,
            start_hhmm=row.start_hhmm,
            end_hhmm=row.end_hhmm,
            code=row.code,
        )
    except ValueError as e:
        logger.warning(f"Помилка валідації: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Несподівана помилка при оновленні комірки графіку")
        raise HTTPException(status_code=500, detail=f"Не вдалося зберегти графік: {str(e)}")


@router.post("", response_model=ScheduleBatchResponse)
def batch_upsert_schedule(payload: ScheduleBatchUpsert, db: Session = Depends(get_db)):
    """
    Масове збереження комірок графіку.
    
    Приймає список комірок і намагається зберегти кожну.
    Повертає статистику: скільки успішно, скільки з помилками.
    
    Приклад запиту:
    ```json
    {
      "cells": [
        {"employee_id": 1, "day": "2026-01-02", "code": "8-17"},
        {"employee_id": 2, "day": "2026-01-02", "start_hhmm": "09:00", "end_hhmm": "18:00"}
      ]
    }
    ```
    """
    success_count = 0
    failed_count = 0
    errors = []
    
    for idx, cell in enumerate(payload.cells):
        try:
            schedule_crud.upsert_cell(
                db=db,
                employee_id=cell.employee_id,
                day=cell.day,
                start_hhmm=cell.start_hhmm,
                end_hhmm=cell.end_hhmm,
                code=cell.code,
            )
            success_count += 1
        except ValueError as e:
            failed_count += 1
            errors.append({
                "index": idx,
                "employee_id": cell.employee_id,
                "day": str(cell.day),
                "error": str(e),
            })
            logger.warning(f"Помилка валідації для комірки {idx}: {e}")
        except Exception as e:
            failed_count += 1
            errors.append({
                "index": idx,
                "employee_id": cell.employee_id,
                "day": str(cell.day),
                "error": f"Несподівана помилка: {str(e)}",
            })
            logger.exception(f"Несподівана помилка для комірки {idx}")
    
    return ScheduleBatchResponse(
        success=success_count,
        failed=failed_count,
        errors=errors,
    )


@router.delete("/cell")
def delete_schedule_cell(
    employee_id: int = Query(..., description="ID працівника"),
    day: date = Query(..., description="День"),
    db: Session = Depends(get_db),
):
    """Видалити комірку графіку."""
    try:
        deleted = schedule_crud.delete_cell(db, employee_id=employee_id, day=day)
        if deleted:
            return {"ok": True, "message": "Комірку видалено"}
        else:
            return {"ok": False, "message": "Комірку не знайдено"}
    except Exception as e:
        logger.exception("Помилка видалення комірки графіку")
        raise HTTPException(status_code=500, detail=f"Не вдалося видалити комірку: {str(e)}")


@router.get("/pdf")
def schedule_pdf(
        date_from: date = Query(..., description="Дата початку"),
        date_to: date = Query(..., description="Дата закінчення"),
        db: Session = Depends(get_db),
):
    """
    Експорт графіку в PDF.

    Генерує PDF-файл з графіком всіх працівників за вказаний період.
    """
    # ── Brand palette ──────────────────────────────────────────────────────────
    C_PRIMARY      = colors.HexColor("#1a2e4a")   # dark navy  — header bg
    C_PRIMARY_LIGHT= colors.HexColor("#243d60")   # slightly lighter navy
    C_ACCENT       = colors.HexColor("#2980b9")   # steel blue — sub-header bg
    C_ACCENT_LIGHT = colors.HexColor("#3498db")   # lighter blue
    C_WEEKEND_H    = colors.HexColor("#c0392b")   # red — weekend header
    C_WEEKEND_D    = colors.HexColor("#fff0f0")   # pale red — weekend data rows
    C_ROW_ODD      = colors.HexColor("#f7f9fc")   # very light blue-grey
    C_ROW_EVEN     = colors.white
    C_BORDER       = colors.HexColor("#c8d6e5")   # soft border
    C_BORDER_DARK  = colors.HexColor("#1a2e4a")   # dark outer border
    C_TEXT_LIGHT   = colors.white
    C_TEXT_MUTED   = colors.HexColor("#6b7a8d")
    C_SHADOW       = colors.HexColor("#e8eef5")   # thin shadow row

    try:
        # ── Font registration (Cyrillic-capable) ────────────────────────────
        FONT_PATHS = [
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ("/usr/local/lib/python3.12/site-packages/cv2/qt/fonts/DejaVuSans.ttf",
             "/usr/local/lib/python3.12/site-packages/cv2/qt/fonts/DejaVuSans-Bold.ttf"),
            ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
        ]
        font_name = "Helvetica"
        font_bold = "Helvetica-Bold"
        for reg_path, bold_path in FONT_PATHS:
            try:
                pdfmetrics.registerFont(TTFont("_PDF_Sans", reg_path))
                pdfmetrics.registerFont(TTFont("_PDF_Sans_Bold", bold_path))
                font_name = "_PDF_Sans"
                font_bold = "_PDF_Sans_Bold"
                break
            except Exception:
                continue
        if font_name == "Helvetica":
            logger.warning("Cyrillic font not found, falling back to Helvetica")

        # ── Data collection ─────────────────────────────────────────────────
        employees = employee_crud.get_all(db)
        rows = schedule_crud.get_range(db, date_from=date_from, date_to=date_to, employee_id=None)

        idx: dict[tuple[int, date], tuple[str | None, str | None, str | None]] = {}
        for r in rows:
            idx[(r.employee_id, r.day)] = (r.start_hhmm, r.end_hhmm, r.code)

        days = list(_daterange(date_from, date_to))
        num_days = len(days)
        _DAY_NAMES_UA = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

        # ── Column widths ───────────────────────────────────────────────────
        PAGE_W = landscape(A4)[0]
        MARGIN = 12 * mm
        available_width = PAGE_W - 2 * MARGIN

        COL_NUM  = 10 * mm
        COL_NAME = 52 * mm
        COL_POS  = 36 * mm
        fixed_w  = COL_NUM + COL_NAME + COL_POS

        # Adaptive day-column width: tighter for many days
        day_w_max  = 14 * mm
        day_w_min  = 6.5 * mm
        day_width  = max(day_w_min, min(day_w_max, (available_width - fixed_w) / max(num_days, 1)))
        col_widths = [COL_NUM, COL_NAME, COL_POS] + [day_width] * num_days

        # ── Table data ──────────────────────────────────────────────────────
        # Row-0: date numbers | Row-1: weekday abbreviations
        header_row1 = ["№", "Прізвище та ім'я", "Посада"] + [d.strftime("%d") for d in days]
        header_row2 = ["", "", ""] + [_DAY_NAMES_UA[d.weekday()] for d in days]
        data: list[list[str]] = [header_row1, header_row2]

        for i, e in enumerate(employees, start=1):
            row: list[str] = [str(i), e.full_name, (e.position or "—")]
            for d in days:
                s, en, code = idx.get((e.id, d), (None, None, None))
                row.append(_time_cell(s, en, code))
            data.append(row)

        # ── PDF document ────────────────────────────────────────────────────
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=14 * mm,
            bottomMargin=12 * mm,
            title=f"Графік змін {date_from.strftime('%d.%m.%Y')}–{date_to.strftime('%d.%m.%Y')}",
            author="TimeTracker",
            subject="Графік роботи персоналу",
        )

        # ── Paragraph styles ────────────────────────────────────────────────
        def _ps(name, font, size, color, align=TA_LEFT, leading=None, space_before=0, space_after=0):
            return ParagraphStyle(
                name,
                fontName=font,
                fontSize=size,
                textColor=color,
                alignment=align,
                leading=leading or size * 1.25,
                spaceBefore=space_before,
                spaceAfter=space_after,
            )

        sTitle    = _ps("Title",    font_bold, 16, C_PRIMARY,    TA_CENTER, space_before=0, space_after=1*mm)
        sSubtitle = _ps("Subtitle", font_name,  9, C_TEXT_MUTED, TA_CENTER, space_before=0, space_after=4*mm)
        sFooter   = _ps("Footer",   font_name,  7, C_TEXT_MUTED, TA_RIGHT)

        # ── Page-number callback ─────────────────────────────────────────────
        generated_at = dt.now().strftime("%d.%m.%Y %H:%M")

        def add_page_meta(canvas, document):
            canvas.saveState()
            # thin top bar
            canvas.setFillColor(C_PRIMARY)
            canvas.rect(MARGIN, landscape(A4)[1] - 8*mm, PAGE_W - 2*MARGIN, 1.2, fill=1, stroke=0)
            # footer line
            canvas.setFillColor(C_BORDER)
            canvas.rect(MARGIN, 8*mm, PAGE_W - 2*MARGIN, 0.5, fill=1, stroke=0)
            # footer text left
            canvas.setFont(font_name, 7)
            canvas.setFillColor(C_TEXT_MUTED)
            canvas.drawString(MARGIN, 5*mm, "TimeTracker — Графік роботи персоналу")
            # footer text right
            page_str = f"Сформовано: {generated_at}   Стор. {document.page}"
            canvas.drawRightString(PAGE_W - MARGIN, 5*mm, page_str)
            canvas.restoreState()

        # ── Story ───────────────────────────────────────────────────────────
        story = []

        story.append(Paragraph(
            f"Графік змін робочих змін",
            sTitle,
        ))
        period_str = (
            f"Період: {date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}"
            f"   |   Співробітників: {len(employees)}"
            f"   |   Днів: {num_days}"
        )
        story.append(Paragraph(period_str, sSubtitle))
        story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceAfter=4*mm))

        # ── Table style ─────────────────────────────────────────────────────
        ts = TableStyle([
            # ── Header row 0: dates ──────────────────────────────────────────
            ("BACKGROUND",   (0, 0), (-1, 0), C_PRIMARY),
            ("TEXTCOLOR",    (0, 0), (-1, 0), C_TEXT_LIGHT),
            ("FONTNAME",     (0, 0), (-1, 0), font_bold),
            ("FONTSIZE",     (0, 0), (-1, 0), 8),
            ("TOPPADDING",   (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING",(0, 0), (-1, 0), 5),

            # ── Header row 1: weekday names ──────────────────────────────────
            ("BACKGROUND",   (0, 1), (-1, 1), C_ACCENT),
            ("TEXTCOLOR",    (0, 1), (-1, 1), C_TEXT_LIGHT),
            ("FONTNAME",     (0, 1), (-1, 1), font_name),
            ("FONTSIZE",     (0, 1), (-1, 1), 6.5),
            ("TOPPADDING",   (0, 1), (-1, 1), 3),
            ("BOTTOMPADDING",(0, 1), (-1, 1), 3),

            # ── First 3 columns bold in header ───────────────────────────────
            ("FONTNAME",     (0, 0), (2, 1), font_bold),

            # ── Data rows ────────────────────────────────────────────────────
            ("FONTNAME",     (0, 2), (-1, -1), font_name),
            ("FONTSIZE",     (0, 2), (-1, -1), 7),
            ("TOPPADDING",   (0, 2), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 2), (-1, -1), 3),

            # ── Alternating row colours ───────────────────────────────────────
            ("ROWBACKGROUNDS", (0, 2), (-1, -1), [C_ROW_EVEN, C_ROW_ODD]),

            # ── Alignment ────────────────────────────────────────────────────
            ("ALIGN",   (0, 0), (0, -1),  "CENTER"),  # №
            ("ALIGN",   (1, 0), (1, -1),  "LEFT"),    # Name
            ("ALIGN",   (2, 0), (2, -1),  "LEFT"),    # Position
            ("ALIGN",   (3, 0), (-1, -1), "CENTER"),  # Days
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),

            # ── Borders ──────────────────────────────────────────────────────
            ("GRID",    (0, 0), (-1, -1),  0.3, C_BORDER),
            ("BOX",     (0, 0), (-1, -1),  1.2, C_BORDER_DARK),
            # thick line under header
            ("LINEBELOW", (0, 1), (-1, 1), 1.5, C_PRIMARY),
            # thick right border after fixed columns
            ("LINEAFTER", (2, 0), (2, -1), 1.2, C_PRIMARY),

            # ── Padding (global) ─────────────────────────────────────────────
            ("LEFTPADDING",  (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ])

        # ── Weekend highlighting ─────────────────────────────────────────────
        for di, d in enumerate(days):
            col = 3 + di
            if d.weekday() >= 5:
                ts.add("BACKGROUND", (col, 0), (col, 0), C_WEEKEND_H)
                ts.add("BACKGROUND", (col, 1), (col, 1), C_WEEKEND_H)
                # For weekend data cells override alternating background
                num_data_rows = len(employees)
                if num_data_rows:
                    ts.add("BACKGROUND", (col, 2), (col, 1 + num_data_rows), C_WEEKEND_D)

        tbl = Table(data, colWidths=col_widths, repeatRows=2)
        tbl.setStyle(ts)
        story.append(tbl)

        # ── Legend ───────────────────────────────────────────────────────────
        story.append(Spacer(1, 5 * mm))
        legend_data = [
            ["Позначення:",
             "В — вихідний",
             "Б — лікарняний",
             "В/Д — відпустка",
             "—  — не заповнено",
             "ЧЧ:ХХ — початок / кінець зміни"],
        ]
        leg_ts = TableStyle([
            ("FONTNAME",    (0, 0), (-1, -1), font_name),
            ("FONTSIZE",    (0, 0), (-1, -1), 7),
            ("TEXTCOLOR",   (0, 0), (0, 0),   C_PRIMARY),
            ("FONTNAME",    (0, 0), (0, 0),   font_bold),
            ("TEXTCOLOR",   (1, 0), (-1, -1), C_TEXT_MUTED),
            ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ])
        leg_widths = [28*mm, 28*mm, 28*mm, 28*mm, 28*mm, 60*mm]
        leg_tbl = Table(legend_data, colWidths=leg_widths)
        leg_tbl.setStyle(leg_ts)
        story.append(leg_tbl)

        # ── Build ────────────────────────────────────────────────────────────
        doc.build(story, onFirstPage=add_page_meta, onLaterPages=add_page_meta)

        buf.seek(0)
        filename = f"grafik_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    except Exception as e:
        logger.exception("Помилка генерації PDF")
        raise HTTPException(status_code=500, detail=f"Не вдалося згенерувати PDF: {str(e)}")


