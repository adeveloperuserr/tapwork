import base64
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import require_role, get_current_user
from ..models import BiometricData, User
from ..database import get_db
from .. import schemas

logger = logging.getLogger(__name__)

# Try to import face recognition utilities - graceful degradation
try:
    from ..utils.face_recognition import (
        extract_face_embedding,
        verify_face,
        NoFaceDetectedError,
        MultipleFacesError,
        LowQualityImageError,
        LivenessCheckFailedError,
        FaceRecognitionError,
    )
    FACE_RECOGNITION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Face recognition not available: {e}")
    FACE_RECOGNITION_AVAILABLE = False

    # Define dummy exceptions for graceful degradation
    class NoFaceDetectedError(Exception):
        pass
    class MultipleFacesError(Exception):
        pass
    class LowQualityImageError(Exception):
        pass
    class LivenessCheckFailedError(Exception):
        pass
    class FaceRecognitionError(Exception):
        pass

admin_or_hr = require_role(["Admin", "HR Manager"])

router = APIRouter(prefix="/api/biometric", tags=["biometric"])


# ============================================================================
# ENDPOINTS PARA USUARIOS (RECONOCIMIENTO FACIAL)
# ============================================================================

@router.post("/face/register", response_model=schemas.FaceRegistrationResponse)
async def register_face(
    payload: schemas.FaceRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permite al usuario registrar su rostro para autenticación biométrica
    """
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconocimiento facial no disponible. Las dependencias no están instaladas correctamente."
        )

    try:
        # Extraer embedding facial con todas las validaciones
        embedding_bytes = await extract_face_embedding(payload.image_data)

        # Buscar si ya existe un registro facial
        existing = await db.scalar(
            select(BiometricData).where(
                BiometricData.user_id == current_user.id,
                BiometricData.biometric_type == "face"
            )
        )

        if existing:
            # Actualizar embedding existente
            existing.biometric_hash = embedding_bytes
            existing.enrolled_at = datetime.utcnow()
            logger.info(f"Face embedding updated for user {current_user.email}")
        else:
            # Crear nuevo registro
            new_biometric = BiometricData(
                user_id=current_user.id,
                biometric_type="face",
                biometric_hash=embedding_bytes,
            )
            db.add(new_biometric)
            logger.info(f"Face embedding registered for user {current_user.email}")

        try:
            await db.commit()
        except Exception as commit_error:
            # Manejar race condition - si otro request ya insertó, actualizar en su lugar
            if "duplicate key" in str(commit_error).lower() or "unique constraint" in str(commit_error).lower():
                await db.rollback()
                logger.warning(f"Race condition detected for user {current_user.email}, retrying as update...")

                # Refrescar y buscar el registro que ya existe
                existing = await db.scalar(
                    select(BiometricData).where(
                        BiometricData.user_id == current_user.id,
                        BiometricData.biometric_type == "face"
                    )
                )

                if existing:
                    existing.biometric_hash = embedding_bytes
                    existing.enrolled_at = datetime.utcnow()
                    await db.commit()
                    logger.info(f"Face embedding updated after race condition for user {current_user.email}")
                else:
                    raise  # Si aún no existe, re-lanzar el error original
            else:
                raise  # Re-lanzar otros errores de commit

        return schemas.FaceRegistrationResponse(
            success=True,
            message="Rostro registrado exitosamente",
            face_detected=True,
            quality_score=0.95  # Placeholder - ya pasó las validaciones de calidad
        )

    except NoFaceDetectedError as e:
        logger.warning(f"No face detected for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MultipleFacesError as e:
        logger.warning(f"Multiple faces detected for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LowQualityImageError as e:
        logger.warning(f"Low quality image for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LivenessCheckFailedError as e:
        logger.warning(f"Liveness check failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FaceRecognitionError as e:
        logger.error(f"Face recognition error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando imagen: {str(e)}"
        )


@router.get("/face/status")
async def get_face_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica si el usuario tiene un rostro registrado
    """
    biometric = await db.scalar(
        select(BiometricData).where(
            BiometricData.user_id == current_user.id,
            BiometricData.biometric_type == "face"
        )
    )

    return {
        "has_face_registered": biometric is not None,
        "enrolled_at": biometric.enrolled_at.isoformat() if biometric else None,
        "last_verified_at": biometric.last_verified_at.isoformat() if biometric and biometric.last_verified_at else None
    }


@router.delete("/face")
async def delete_face(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina el registro facial del usuario
    """
    biometric = await db.scalar(
        select(BiometricData).where(
            BiometricData.user_id == current_user.id,
            BiometricData.biometric_type == "face"
        )
    )

    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes un rostro registrado"
        )

    await db.delete(biometric)
    await db.commit()

    logger.info(f"Face registration deleted for user {current_user.email}")

    return {"detail": "Registro facial eliminado exitosamente"}


# ============================================================================
# ENDPOINTS PARA ADMIN/HR (LEGACY)
# ============================================================================

@router.post("/enroll", response_model=schemas.BiometricEnrollment, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_or_hr)])
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


@router.delete("/{biometric_id}", dependencies=[Depends(admin_or_hr)])
async def delete_biometric(biometric_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    biometric = await db.scalar(select(BiometricData).where(BiometricData.id == biometric_id))
    if not biometric:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    await db.delete(biometric)
    await db.commit()
    return {"detail": "Eliminado"}

