import io
import secrets
from datetime import datetime, timedelta, timezone

import qrcode


def generate_code_data() -> str:
    return secrets.token_urlsafe(16)


def generate_qr_png(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def default_expiration(days: int = 365) -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days)

