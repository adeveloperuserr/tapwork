from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user
from ..models import QRCode, User
from ..utils.barcode import generate_qr_png
from ..database import get_db

router = APIRouter(prefix="/api/barcodes", tags=["barcodes"])


@router.get("/me.png")
async def my_barcode(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QRCode).where(QRCode.user_id == current_user.id))
    qr = result.scalar_one_or_none()
    if not qr or not qr.is_active:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    png = generate_qr_png(qr.code_data)
    return Response(content=png, media_type="image/png")

