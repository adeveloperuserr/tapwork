import secrets
import string
from datetime import datetime, timedelta, timezone


def generate_secure_password(length: int = 12) -> str:
    """
    Genera una contraseña segura aleatoria.

    Args:
        length: Longitud de la contraseña (mínimo 8, default 12)

    Returns:
        Contraseña segura que incluye mayúsculas, minúsculas, números y símbolos
    """
    if length < 8:
        length = 8

    # Caracteres a usar
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%&*-_=+"

    # Asegurar al menos un carácter de cada tipo
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]

    # Rellenar el resto con caracteres aleatorios
    all_chars = lowercase + uppercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Mezclar para que no sea predecible
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def generate_reset_token() -> str:
    """
    Genera un token seguro para reseteo de contraseña.

    Returns:
        Token URL-safe de 32 bytes
    """
    return secrets.token_urlsafe(32)


def is_password_expired(password_changed_at: datetime | None, days: int = 90) -> bool:
    """
    Verifica si la contraseña ha expirado.

    Args:
        password_changed_at: Fecha del último cambio de contraseña
        days: Días hasta que expire (default 90, equivale a 3 meses)

    Returns:
        True si la contraseña ha expirado o nunca se ha cambiado
    """
    if password_changed_at is None:
        return True

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expiry_date = password_changed_at + timedelta(days=days)

    return now >= expiry_date


def is_token_expired(token_expires: datetime | None) -> bool:
    """
    Verifica si un token de reseteo ha expirado.

    Args:
        token_expires: Fecha de expiración del token

    Returns:
        True si el token ha expirado o no existe
    """
    if token_expires is None:
        return True

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now >= token_expires
