import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from .. import schemas
from ..dependencies import get_current_user
from ..models import AuditLog, QRCode, Role, User
from ..utils import barcode
from ..utils.email import build_reset_email, build_verification_email, send_email
from ..utils.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    hash_password,
    verify_password,
)
from ..database import get_db

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
    )
    db.add(user)
    await db.flush()

    qr = QRCode(user_id=user.id, code_data=barcode.generate_code_data(), expires_at=barcode.default_expiration(), is_active=True)
    db.add(qr)
    await db.commit()
    await db.refresh(user)

    verify_token = create_email_verification_token(str(user.id))
    if user.notification_preferences.get("registration", True):
        subject, recipient, html = build_verification_email(user.email, verify_token)
        await send_email(subject, recipient, "Verifica tu correo", html)

    await _log(db, user.id, "CREATE", "user", {"user": str(user.id)}, ip_address=request.client.host if request.client else None)
    tokens = schemas.AuthTokens(access_token=create_access_token(str(user.id)))
    return schemas.AuthResponse(user=user, tokens=tokens)


@router.post("/login", response_model=schemas.AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    tokens = schemas.AuthTokens(access_token=create_access_token(str(user.id)))
    return schemas.AuthResponse(user=user, tokens=tokens)


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
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"detail": "Si el correo existe, se enviará un enlace"}
    reset_token = create_password_reset_token(str(user.id))
    if user.notification_preferences.get("reset", True):
        subject, recipient, html = build_reset_email(user.email, reset_token)
        await send_email(subject, recipient, "Restablecer contraseña", html)
    await _log(db, user.id, "REQUEST_RESET", "user", None, ip_address=request.client.host if request.client else None)
    return {"detail": "Si el correo existe, se enviará un enlace"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: Request, payload: schemas.PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    try:
        data = create_token_payload(payload.token, expected_type="reset")
    except ValueError:
        raise HTTPException(status_code=400, detail="Token inválido")
    user_id = data.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    await _log(db, user.id, "RESET", "user", None, ip_address=request.client.host if request.client else None)
    return {"detail": "Contraseña actualizada"}


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

