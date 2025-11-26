import logging
from email.message import EmailMessage

import aiosmtplib

from ..config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(subject: str, recipient: str, body: str, html: str | None = None) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=settings.smtp_tls,
        )
    except Exception:
        logger.exception("Failed to send email")
        # Surface a soft failure to keep flows working locally


def build_verification_email(email: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.frontend_base_url}/verify-email?token={token}"
    subject = "Verifica tu correo"
    body = f"Hola,\nConfirma tu correo haciendo clic en: {link}"
    html = f"<p>Hola,</p><p>Confirma tu correo haciendo clic en <a href='{link}'>este enlace</a>.</p>"
    return subject, email, html if html else body


def build_reset_email(email: str, token: str) -> tuple[str, str, str]:
    link = f"{settings.frontend_base_url}/reset-password?token={token}"
    subject = "Restablecer contraseña"
    body = f"Para restablecer tu contraseña usa el siguiente enlace: {link}"
    html = f"<p>Para restablecer tu contraseña, usa <a href='{link}'>este enlace</a>.</p>"
    return subject, email, html if html else body


def build_attendance_alert(email: str, status: str, notes: str | None = None) -> tuple[str, str, str]:
    subject = f"Alerta de asistencia: {status}"
    body = f"Tu registro de asistencia tiene estado: {status}." + (f" Nota: {notes}" if notes else "")
    html = f"<p>Tu registro de asistencia tiene estado: <strong>{status}</strong>.</p>"
    if notes:
        html += f"<p>{notes}</p>"
    return subject, email, html

