import logging
from email.message import EmailMessage

import aiosmtplib

from ..config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(subject: str, recipient: str, body: str, html: str | None = None, attachments: list[tuple[str, bytes, str]] | None = None) -> None:
    """
    Envía un email con soporte para adjuntos.

    Args:
        subject: Asunto del email
        recipient: Destinatario
        body: Cuerpo en texto plano
        html: Cuerpo en HTML (opcional)
        attachments: Lista de tuplas (filename, content, mimetype) para adjuntar (opcional)
    """
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")

    # Agregar adjuntos si existen
    if attachments:
        for filename, content, mimetype in attachments:
            maintype, subtype = mimetype.split('/')
            message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

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


def build_welcome_email(email: str, first_name: str, employee_id: str) -> tuple[str, str, str]:
    """
    Construye el email de bienvenida con instrucciones sobre el código de barras.
    El código de barras se envía como adjunto separado.
    """
    subject = f"Bienvenido a Tapwork - Tu código de barras"
    body = f"""Hola {first_name},

¡Bienvenido a Tapwork!

Tu cuenta ha sido creada exitosamente. Tu identificador de empleado es: {employee_id}

En este email encontrarás adjunto tu código de barras personal. Este código es único y te identifica en el sistema de asistencia.

Instrucciones:
1. Guarda el código de barras adjunto en un lugar seguro
2. Puedes imprimirlo o guardarlo en tu dispositivo móvil
3. Usa este código para registrar tu entrada y salida
4. Escanea el código en las terminales de asistencia

Si tienes alguna pregunta, no dudes en contactar a tu supervisor.

Saludos,
El equipo de Tapwork"""

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .employee-id {{ background: #667eea; color: white; padding: 15px; border-radius: 5px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0; }}
            .instructions {{ background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; }}
            .instructions li {{ margin: 10px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>¡Bienvenido a Tapwork!</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{first_name}</strong>,</p>
                <p>Tu cuenta ha sido creada exitosamente.</p>

                <div class="employee-id">
                    ID: {employee_id}
                </div>

                <p>En este email encontrarás adjunto tu <strong>código de barras personal</strong>. Este código es único y te identifica en el sistema de asistencia.</p>

                <div class="instructions">
                    <h3>📋 Instrucciones:</h3>
                    <ol>
                        <li>Guarda el código de barras adjunto en un lugar seguro</li>
                        <li>Puedes imprimirlo o guardarlo en tu dispositivo móvil</li>
                        <li>Usa este código para registrar tu entrada y salida</li>
                        <li>Escanea el código en las terminales de asistencia</li>
                    </ol>
                </div>

                <p>Si tienes alguna pregunta, no dudes en contactar a tu supervisor.</p>

                <p>Saludos,<br><strong>El equipo de Tapwork</strong></p>
            </div>
            <div class="footer">
                <p>Este es un mensaje automático, por favor no responder.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return subject, email, html

