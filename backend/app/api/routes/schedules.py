from __future__ import annotations

from datetime import date, timedelta
from calendar import monthrange
from io import BytesIO
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

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
    try:
        # Реєструємо шрифт з підтримкою кирилиці
        try:
            # Спробуємо використати системний шрифт
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            font_name = 'DejaVuSans'
        except:
            try:
                # Альтернативний шлях для Windows
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                font_name = 'Arial'
            except:
                # Якщо нічого не знайдено - використовуємо Helvetica (без кирилиці)
                font_name = 'Helvetica'
                logger.warning("Не знайдено шрифт з підтримкою кирилиці, використовується Helvetica")

        employees = employee_crud.get_all(db)
        rows = schedule_crud.get_range(db, date_from=date_from, date_to=date_to, employee_id=None)

        # Індексуємо по (employee_id, day) -> (start, end, code)
        idx: dict[tuple[int, date], tuple[str | None, str | None, str | None]] = {}
        for r in rows:
            idx[(r.employee_id, r.day)] = (r.start_hhmm, r.end_hhmm, r.code)

        days = list(_daterange(date_from, date_to))

        # Формуємо заголовки
        header = ["№", "ПІБ", "Посада"] + [d.strftime("%d") for d in days]
        data: list[list[str]] = [header]

        # Формуємо рядки для кожного співробітника
        for i, e in enumerate(employees, start=1):
            row: list[str] = [str(i), e.full_name, (e.position or "—")]
            for d in days:
                start_hhmm, end_hhmm, code = idx.get((e.id, d), (None, None, None))
                cell_text = _time_cell(start_hhmm, end_hhmm, code)
                row.append(cell_text)
            data.append(row)

        # Створюємо PDF
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title="Графік роботи",
        )

        # Стилі
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        if font_name != 'Helvetica':
            title_style.fontName = font_name

        story = []

        # Заголовок
        title = Paragraph(
            f"Графік змін: {date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}",
            title_style
        )
        story.append(title)
        story.append(Spacer(1, 10 * mm))

        # Розрахунок ширини колонок
        num_days = len(days)
        available_width = landscape(A4)[0] - 20 * mm  # Віднімаємо поля

        # Фіксовані ширини для перших колонок
        col_widths = [
            15 * mm,  # №
            50 * mm,  # ПІБ
            40 * mm,  # Посада
        ]

        # Решта простору для днів
        remaining_width = available_width - sum(col_widths)
        day_width = remaining_width / num_days
        col_widths.extend([day_width] * num_days)

        # Створюємо таблицю
        tbl = Table(data, colWidths=col_widths, repeatRows=1)

        # Стилі таблиці
        table_style = [
            # Заголовок
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a90e2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), font_name),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 0), (0, 0), font_name),  # №

            # Дані
            ("FONTNAME", (0, 1), (-1, -1), font_name),
            ("FONTSIZE", (0, 1), (-1, -1), 7),

            # Вирівнювання
            ("ALIGN", (0, 0), (0, -1), "CENTER"),  # №
            ("ALIGN", (1, 0), (2, -1), "LEFT"),  # ПІБ, Посада
            ("ALIGN", (3, 0), (-1, -1), "CENTER"),  # Дні
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            # Рамки
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),

            # Чергування кольорів
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),

            # Відступи
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]

        tbl.setStyle(TableStyle(table_style))
        story.append(tbl)

        # Генерація PDF
        doc.build(story)

        buf.seek(0)
        filename = f"grafik_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )

    except Exception as e:
        logger.exception("Помилка генерації PDF")
        raise HTTPException(status_code=500, detail=f"Не вдалося згенерувати PDF: {str(e)}")


