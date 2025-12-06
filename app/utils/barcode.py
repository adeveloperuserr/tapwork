import io
from datetime import datetime, timedelta, timezone

import barcode
from barcode.writer import ImageWriter


def generate_code_data(employee_id: str) -> str:
    """
    Genera el código de barras usando el employee_id del usuario.
    Esto da sentido de pertenencia ya que cada código es único y reconocible.
    """
    return employee_id


def generate_barcode_png(employee_id: str) -> bytes:
    """
    Genera una imagen PNG de código de barras Code128 a partir del employee_id.
    Code128 es ideal para employee IDs ya que soporta números, letras y caracteres especiales.
    """
    code128 = barcode.get_barcode_class('code128')
    barcode_instance = code128(employee_id, writer=ImageWriter())

    buffer = io.BytesIO()
    barcode_instance.write(buffer, options={
        'module_width': 0.3,
        'module_height': 15.0,
        'quiet_zone': 6.5,
        'font_size': 10,
        'text_distance': 5.0,
        'background': 'white',
        'foreground': 'black',
    })
    buffer.seek(0)
    return buffer.read()


def default_expiration(days: int = 365) -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days)

