import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..dependencies import get_current_user
from ..models import AttendanceRecord, User
from ..utils.security import hash_password, verify_password
from ..utils.email import build_welcome_email, send_email
from ..utils import barcode
from ..database import get_db

router = APIRouter(prefix="/api/user", tags=["user"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permite al usuario cambiar su propia contraseña"""
    # Verificar contraseña actual
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    current_user.password_hash = hash_password(payload.new_password)
    await db.commit()

    return {"detail": "Contraseña actualizada exitosamente"}


@router.post("/resend-barcode")
async def resend_barcode(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reenvía el código de barras del usuario a su email"""
    if not current_user.notification_preferences.get("registration", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las notificaciones por email están deshabilitadas"
        )

    # Construir email
    subject, recipient, html = build_welcome_email(
        current_user.email,
        current_user.first_name,
        current_user.employee_id
    )

    # Generar barcode PNG
    barcode_png = barcode.generate_barcode_png(current_user.employee_id)

    # Enviar email
    await send_email(
        subject,
        recipient,
        f"Tu código de barras - {current_user.employee_id}",
        html,
        attachments=[(f"barcode_{current_user.employee_id}.png", barcode_png, "image/png")]
    )

    return {"detail": "Código de barras enviado a tu email"}


@router.get("/attendance-history")
async def get_attendance_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el historial de asistencias del usuario actual (últimos 30 días)"""
    # Calcular fecha de hace 30 días
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Consultar registros
    result = await db.execute(
        select(AttendanceRecord)
        .where(AttendanceRecord.user_id == current_user.id)
        .where(AttendanceRecord.check_in >= thirty_days_ago)
        .order_by(AttendanceRecord.check_in.desc())
    )

    records = result.scalars().all()

    return [
        {
            "id": str(record.id),
            "check_in": record.check_in.isoformat(),
            "check_out": record.check_out.isoformat() if record.check_out else None,
            "date": record.check_in.date().isoformat(),
        }
        for record in records
    ]
