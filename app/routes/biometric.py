import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import require_role
from ..models import BiometricData, User
from ..database import get_db
from .. import schemas

admin_or_hr = require_role(["Admin", "HR Manager"])

router = APIRouter(prefix="/api/biometric", tags=["biometric"], dependencies=[Depends(admin_or_hr)])


@router.post("/enroll", response_model=schemas.BiometricEnrollment, status_code=status.HTTP_201_CREATED)
async def enroll(payload: schemas.BiometricEnrollment, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id == payload.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    hashed = base64.b64decode(payload.biometric_hash.encode())
    existing = await db.scalar(
        select(BiometricData).where(BiometricData.user_id == payload.user_id, BiometricData.biometric_type == payload.biometric_type)
    )
    if existing:
        existing.biometric_hash = hashed
    else:
        db.add(
            BiometricData(
                user_id=payload.user_id,
                biometric_type=payload.biometric_type,
                biometric_hash=hashed,
            )
        )
    await db.commit()
    return payload


@router.delete("/{biometric_id}")
async def delete_biometric(biometric_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    biometric = await db.scalar(select(BiometricData).where(BiometricData.id == biometric_id))
    if not biometric:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    await db.delete(biometric)
    await db.commit()
    return {"detail": "Eliminado"}

