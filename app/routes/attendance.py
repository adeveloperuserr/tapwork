from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..dependencies import get_current_user
from ..models import AttendanceRecord, QRCode, User
from ..utils.email import build_attendance_alert, send_email
from ..database import get_db

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


async def _status_for_check_in(user: User, check_in: datetime) -> str:
    if not user.shift:
        return "on-time"
    start_dt = datetime.combine(check_in.date(), user.shift.start_time)
    if check_in > start_dt + timedelta(minutes=user.shift.grace_period_minutes):
        return "late"
    return "on-time"


@router.post("/scan", response_model=schemas.AttendanceOut)
async def scan_attendance(payload: schemas.AttendanceCreate, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # Naive datetime para PostgreSQL
    qr_result = await db.execute(
        select(QRCode)
        .where(QRCode.code_data == payload.code_data)
        .where(QRCode.is_active.is_(True))
        .where((QRCode.expires_at.is_(None)) | (QRCode.expires_at > now))
    )
    qr = qr_result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="Código no válido")

    user_result = await db.execute(select(User).where(User.id == qr.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    if payload.action == "check_in":
        status = await _status_for_check_in(user, now)
        record = AttendanceRecord(
            user_id=user.id,
            check_in=now,
            status=status,
            location=payload.location,
            notes=payload.notes,
            shift_id=user.shift_id,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
    else:
        last_result = await db.execute(
            select(AttendanceRecord)
            .where(and_(AttendanceRecord.user_id == user.id, AttendanceRecord.check_out.is_(None)))
            .order_by(AttendanceRecord.check_in.desc())
        )
        record = last_result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=400, detail="No hay check-in abierto")
        record.check_out = now
        record.notes = payload.notes or record.notes
        await db.commit()
        await db.refresh(record)

    if user.notification_preferences.get("attendance", True):
        subject, recipient, html = build_attendance_alert(user.email, record.status, payload.notes)
        await send_email(subject, recipient, "Alerta de asistencia", html)

    return record


@router.get("/me", response_model=list[schemas.AttendanceOut])
async def my_attendance(
    start: datetime = Query(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)),
    end: datetime = Query(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)),
    limit: int = Query(default=100, le=500, description="Máximo de registros a retornar"),
    offset: int = Query(default=0, ge=0, description="Offset para paginación"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.user_id == current_user.id)
        .where(AttendanceRecord.check_in >= start)
        .where(AttendanceRecord.check_in <= end)
        .order_by(AttendanceRecord.check_in.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()

