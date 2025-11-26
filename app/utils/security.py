from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict[str, Any], expires_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def create_access_token(user_id: str) -> str:
    return create_token({"sub": user_id, "type": "access"}, settings.access_token_exp_minutes)


def create_email_verification_token(user_id: str) -> str:
    return create_token({"sub": user_id, "type": "verify"}, settings.email_verification_token_exp_minutes)


def create_password_reset_token(user_id: str) -> str:
    return create_token({"sub": user_id, "type": "reset"}, settings.password_reset_token_exp_minutes)

