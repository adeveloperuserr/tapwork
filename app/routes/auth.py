import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from slowapi import Limiter
from slowapi.util import get_remote_address

from .. import schemas
from ..dependencies import get_current_user
from ..models import AuditLog, BiometricData, QRCode, Role, User
from ..utils import barcode
from ..utils.email import build_reset_email, build_verification_email, build_welcome_email, send_email
from ..utils.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    hash_password,
    verify_password,
)
from ..utils.password import is_password_expired
from ..database import get_db

logger = logging.getLogger(__name__)

# Try to import face recognition utilities - graceful degradation
try:
    from ..utils.face_recognition import (
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

    # Define dummy exceptions
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

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


async def _log(db: AsyncSession, user_id: uuid.UUID | None, action: str, resource: str, changes: dict | None = None, ip_address: str | None = None):
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, changes=changes, ip_address=ip_address))
    await db.commit()


@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, payload: schemas.RegistrationRequest, db: AsyncSession = Depends(get_db)):
    # Validate unique email and employee
    existing = await db.execute(select(User).where((User.email == payload.email) | (User.employee_id == payload.employee_id)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email o empleado ya existen")

    default_role = await db.scalar(select(Role).where(Role.name == "Employee"))

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        employee_id=payload.employee_id,
        role=default_role,
        department_id=payload.department_id,
        shift_id=payload.shift_id,
        notification_preferences=payload.notification_preferences,
        password_reset_required=True,  # Requerir cambio en primer login
        password_changed_at=None,  # Nunca ha cambiado la contraseña
    )
    db.add(user)
    await db.flush()

    # Generar código de barras usando el employee_id para sentido de pertenencia
    barcode_code = QRCode(
        user_id=user.id,
        code_data=barcode.generate_code_data(user.employee_id),
        expires_at=barcode.default_expiration(),
        is_active=True
    )
    db.add(barcode_code)
    await db.commit()
    await db.refresh(user)

    # Enviar emails de verificación y bienvenida
    if user.notification_preferences.get("registration", True):
        # Email de verificación
        verify_token = create_email_verification_token(str(user.id))
        subject, recipient, html = build_verification_email(user.email, verify_token)
        await send_email(subject, recipient, "Verifica tu correo", html)

        # Email de bienvenida con código de barras adjunto
        subject_welcome, recipient_welcome, html_welcome = build_welcome_email(
            user.email, user.first_name, user.employee_id
        )
        barcode_png = barcode.generate_barcode_png(user.employee_id)
        await send_email(
            subject_welcome,
            recipient_welcome,
            f"Bienvenido {user.first_name}",
            html_welcome,
            attachments=[(f"barcode_{user.employee_id}.png", barcode_png, "image/png")]
        )

    await _log(db, user.id, "CREATE", "user", {"user": str(user.id)}, ip_address=request.client.host if request.client else None)
    tokens = schemas.AuthTokens(access_token=create_access_token(str(user.id)))
    return schemas.AuthResponse(user=user, tokens=tokens)


@router.post("/login", response_model=schemas.AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .where(User.email == payload.email)
        .options(
            selectinload(User.role),
            selectinload(User.department),
            selectinload(User.shift)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Verificar si la contraseña expiró (cada 3 meses = 90 días)
    password_expired = is_password_expired(user.password_changed_at, days=90)

    # Verificar si requiere cambio de contraseña (primer login o expiración)
    needs_password_change = user.password_reset_required or password_expired

    tokens = schemas.AuthTokens(access_token=create_access_token(str(user.id)))
    return schemas.AuthResponse(
        user=user,
        tokens=tokens,
        password_reset_required=needs_password_change
    )


@router.post("/login/face", response_model=schemas.AuthResponse)
@limiter.limit("5/minute")
async def login_with_face(request: Request, payload: schemas.FaceLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login usando reconocimiento facial
    Sistema de autenticación biométrica de nivel bancario
    """
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconocimiento facial no disponible. Las dependencias no están instaladas correctamente."
        )

    try:
        # Buscar usuario por email
        result = await db.execute(
            select(User)
            .where(User.email == payload.email)
            .options(
                selectinload(User.role),
                selectinload(User.department),
                selectinload(User.shift)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Face login attempt for non-existent user: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        if not user.is_active:
            logger.warning(f"Face login attempt for inactive user: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )

        # Verificar que el usuario tenga un rostro registrado
        biometric = await db.scalar(
            select(BiometricData).where(
                BiometricData.user_id == user.id,
                BiometricData.biometric_type == "face"
            )
        )

        if not biometric:
            logger.warning(f"Face login attempt for user without registered face: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tienes un rostro registrado. Por favor registra tu rostro primero."
            )

        # Verificar el rostro
        is_match, confidence = await verify_face(payload.image_data, biometric.biometric_hash)

        if not is_match:
            logger.warning(
                f"Face verification failed for user {payload.email}: "
                f"confidence={confidence:.2f}%"
            )
            await _log(
                db, user.id, "FAILED_FACE_LOGIN", "auth",
                {"confidence": confidence, "reason": "face_mismatch"},
                ip_address=request.client.host if request.client else None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Verificación facial fallida. El rostro no coincide."
            )

        # Actualizar timestamp de última verificación
        biometric.last_verified_at = datetime.utcnow()
        await db.commit()

        # Login exitoso
        logger.info(f"Successful face login for user {payload.email} (confidence: {confidence:.2f}%)")
        await _log(
            db, user.id, "FACE_LOGIN", "auth",
            {"confidence": confidence, "method": "facial_recognition"},
            ip_address=request.client.host if request.client else None
        )

        tokens = schemas.AuthTokens(access_token=create_access_token(str(user.id)))
        return schemas.AuthResponse(user=user, tokens=tokens)

    except NoFaceDetectedError as e:
        logger.warning(f"No face detected during login for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MultipleFacesError as e:
        logger.warning(f"Multiple faces detected during login for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LowQualityImageError as e:
        logger.warning(f"Low quality image during login for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LivenessCheckFailedError as e:
        logger.warning(f"Liveness check failed during login for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FaceRecognitionError as e:
        logger.error(f"Face recognition error during login for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando imagen: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(request: Request, payload: schemas.EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = verify_email_token(payload.token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")

    user_id = data.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_email_verified = True
    await db.commit()
    await _log(db, user.id, "VERIFY", "user", {"verified": True}, ip_address=request.client.host if request.client else None)
    return {"detail": "Correo verificado"}


def verify_email_token(token: str) -> dict:
    data = create_token_payload(token, expected_type="verify")
    return data


def create_token_payload(token: str, expected_type: str) -> dict:
    from ..utils.security import decode_token

    data = decode_token(token)
    if data.get("type") != expected_type:
        raise ValueError("Tipo de token inválido")
    return data


@router.post("/password-reset")
@limiter.limit("3/minute")
async def request_password_reset(request: Request, payload: schemas.PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta
    from ..utils.password import generate_reset_token

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"detail": "Si el correo existe, se enviará un enlace"}

    # Generar token y guardarlo en la base de datos
    reset_token = generate_reset_token()
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.now() + timedelta(hours=1)  # Expira en 1 hora

    await db.commit()

    if user.notification_preferences.get("reset", True):
        subject, recipient, html = build_reset_email(user.email, reset_token)
        await send_email(subject, recipient, "Restablecer contraseña", html)

    await _log(db, user.id, "REQUEST_RESET", "user", None, ip_address=request.client.host if request.client else None)
    return {"detail": "Si el correo existe, se enviará un enlace"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: Request, payload: schemas.PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    from ..utils.password import is_token_expired

    # Buscar usuario con el token
    result = await db.execute(
        select(User).where(User.password_reset_token == payload.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    # Verificar si el token ha expirado
    if is_token_expired(user.password_reset_expires):
        # Limpiar token expirado
        user.password_reset_token = None
        user.password_reset_expires = None
        await db.commit()
        raise HTTPException(status_code=400, detail="Token expirado. Solicita un nuevo enlace de recuperación")

    # Actualizar contraseña y campos de password management
    user.password_hash = hash_password(payload.new_password)
    user.password_reset_required = False
    user.password_changed_at = datetime.now()
    user.password_reset_token = None
    user.password_reset_expires = None

    await db.commit()
    await _log(db, user.id, "RESET", "user", None, ip_address=request.client.host if request.client else None)
    return {"detail": "Contraseña actualizada"}


@router.post("/change-password")
async def change_password(
    request: Request,
    payload: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cambiar contraseña del usuario autenticado.
    Requiere la contraseña actual y la nueva contraseña.
    """
    # Verificar la contraseña actual
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual incorrecta")

    # Actualizar contraseña y campos de password management
    current_user.password_hash = hash_password(payload.new_password)
    current_user.password_reset_required = False
    current_user.password_changed_at = datetime.now()

    await db.commit()
    await _log(db, current_user.id, "CHANGE_PASSWORD", "user", None, ip_address=request.client.host if request.client else None)

    return {"detail": "Contraseña cambiada exitosamente"}


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

