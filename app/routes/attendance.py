from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from .. import schemas
from ..dependencies import get_current_user
from ..models import AttendanceRecord, QRCode, User, BiometricData
from ..utils.email import build_attendance_alert, send_email
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


async def _status_for_check_in(user: User, check_in: datetime) -> str:
    # User must have eagerly loaded shift relationship
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

    user_result = await db.execute(
        select(User).options(selectinload(User.shift)).where(User.id == qr.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    # LÓGICA AUTOMÁTICA: Detectar si es entrada o salida
    # Buscar si hay un check-in abierto (sin check-out)
    last_result = await db.execute(
        select(AttendanceRecord)
        .where(and_(AttendanceRecord.user_id == user.id, AttendanceRecord.check_out.is_(None)))
        .order_by(AttendanceRecord.check_in.desc())
        .limit(1)  # IMPORTANTE: Solo obtener el último registro
    )
    open_record = last_result.scalar_one_or_none()

    if open_record:
        # Ya hay un check-in abierto → registrar SALIDA
        open_record.check_out = now
        open_record.notes = payload.notes or open_record.notes
        await db.commit()
        await db.refresh(open_record)
        record = open_record
        action_performed = "check_out"
    else:
        # No hay check-in abierto → registrar ENTRADA
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
        action_performed = "check_in"

    if user.notification_preferences.get("attendance", True):
        subject, recipient, html = build_attendance_alert(user.email, record.status, payload.notes)
        await send_email(subject, recipient, "Alerta de asistencia", html)

    return record


@router.post("/biometric-scan", response_model=schemas.AttendanceOut)
async def biometric_scan(
    image: UploadFile = File(...),
    action: str = Form(default="auto"),
    location: str = Form(default=None),
    notes: str = Form(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Registrar asistencia usando reconocimiento facial
    """
    # Try to import face recognition
    try:
        from ..utils.face_recognition import extract_face_embedding, compare_faces
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Reconocimiento facial no disponible. Las dependencias no están instaladas."
        )

    try:
        import base64

        # Read image data
        image_data = await image.read()

        # Convert bytes to base64 string for face recognition
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_base64_str = f"data:image/jpeg;base64,{image_base64}"

        # Extract face embedding from uploaded image
        uploaded_embedding = await extract_face_embedding(image_base64_str)

        # Get all registered face embeddings with eager loading of shift
        result = await db.execute(
            select(BiometricData, User)
            .join(User, BiometricData.user_id == User.id)
            .options(selectinload(User.shift))
            .where(BiometricData.biometric_type == "face")
            .where(User.is_active == True)
        )
        registered_faces = result.all()

        if not registered_faces:
            raise HTTPException(
                status_code=404,
                detail="No hay rostros registrados en el sistema"
            )

        # Find matching user
        matched_user = None
        for biometric, user in registered_faces:
            try:
                is_match = compare_faces(uploaded_embedding, biometric.biometric_hash)
                if is_match:
                    matched_user = user
                    # Update last verified
                    biometric.last_verified_at = datetime.utcnow()
                    break
            except Exception as e:
                logger.warning(f"Error comparing faces for user {user.email}: {e}")
                continue

        if not matched_user:
            raise HTTPException(
                status_code=404,
                detail="Rostro no reconocido. Por favor registra tu rostro primero."
            )

        # Same logic as /scan endpoint - detect check-in or check-out
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        last_result = await db.execute(
            select(AttendanceRecord)
            .where(and_(
                AttendanceRecord.user_id == matched_user.id,
                AttendanceRecord.check_out.is_(None)
            ))
            .order_by(AttendanceRecord.check_in.desc())
            .limit(1)
        )
        open_record = last_result.scalar_one_or_none()

        if open_record:
            # Already checked in → register CHECK-OUT
            open_record.check_out = now
            open_record.notes = notes or open_record.notes
            await db.commit()
            await db.refresh(open_record)
            record = open_record
        else:
            # No open check-in → register CHECK-IN
            status = await _status_for_check_in(matched_user, now)
            record = AttendanceRecord(
                user_id=matched_user.id,
                check_in=now,
                status=status,
                location=location,
                notes=notes,
                shift_id=matched_user.shift_id,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)

        # Send notification if enabled
        if matched_user.notification_preferences.get("attendance", True):
            subject, recipient, html = build_attendance_alert(
                matched_user.email,
                record.status,
                notes
            )
            await send_email(subject, recipient, "Alerta de asistencia", html)

        return record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in biometric scan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando reconocimiento facial: {str(e)}"
        )


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

