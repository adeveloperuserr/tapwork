from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..dependencies import require_role
from ..models import AttendanceRecord, Department, User
from ..utils.reporting import attendance_to_csv, attendance_to_pdf
from ..database import get_db

manager_only = require_role(["Admin", "HR Manager", "Supervisor"])

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(manager_only)])


@router.get("/summary", response_model=schemas.AttendanceSummary)
async def summary(
    start: datetime = Query(...),
    end: datetime = Query(...),
    department_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        func.count(AttendanceRecord.id),
        func.count(case((AttendanceRecord.status == "late", 1))),
    ).where(AttendanceRecord.check_in >= start, AttendanceRecord.check_in <= end)
    if department_id:
        dept_users = select(User.id).where(User.department_id == department_id)
        query = query.where(AttendanceRecord.user_id.in_(dept_users))
    result = await db.execute(query)
    total, late = result.one()
    return schemas.AttendanceSummary(
        total_check_ins=total or 0, late_count=late or 0, range_start=start, range_end=end
    )


@router.post("/export")
async def export_report(payload: schemas.ReportExport, db: AsyncSession = Depends(get_db)):
    records_query = (
        select(
            User.email.label("user_email"),
            AttendanceRecord.check_in,
            AttendanceRecord.check_out,
            AttendanceRecord.status,
            AttendanceRecord.location,
            AttendanceRecord.notes,
        )
        .join(User, User.id == AttendanceRecord.user_id)
        .where(AttendanceRecord.check_in >= payload.range_start, AttendanceRecord.check_in <= payload.range_end)
    )
    if payload.department_id:
        records_query = records_query.where(User.department_id == payload.department_id)

    rows = (await db.execute(records_query)).mappings().all()
    rows_as_dict: list[dict[str, Any]] = [dict(row) for row in rows]

    if payload.format == "csv":
        content = attendance_to_csv(rows_as_dict)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})
    if payload.format == "pdf":
        content = attendance_to_pdf(rows_as_dict)
        return Response(
            content=content, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="report.pdf"'}
        )
    raise HTTPException(status_code=400, detail="Formato no soportado")
