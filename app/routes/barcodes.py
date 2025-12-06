from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user
from ..models import QRCode, User
from ..utils.barcode import generate_barcode_png
from ..database import get_db

router = APIRouter(prefix="/api/barcodes", tags=["barcodes"])


@router.get("/me.png")
async def my_barcode(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Retorna el código de barras del usuario actual como imagen PNG.
    El código de barras es Code128 y contiene el employee_id del usuario.
    """
    result = await db.execute(select(QRCode).where(QRCode.user_id == current_user.id))
    barcode_record = result.scalar_one_or_none()
    if not barcode_record or not barcode_record.is_active:
        raise HTTPException(status_code=404, detail="Código no encontrado")

    # Generar el código de barras usando el employee_id del usuario
    png = generate_barcode_png(current_user.employee_id)
    return Response(content=png, media_type="image/png")

