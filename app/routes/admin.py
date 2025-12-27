import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import schemas
from ..dependencies import require_role
from ..models import Department, Role, Shift, User, QRCode
from ..utils.security import hash_password
from ..utils import barcode
from ..database import get_db

admin_only = require_role(["Admin"])

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(admin_only)])


@router.get("/users", response_model=list[schemas.UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.department),
            selectinload(User.shift)
        )
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Generar employee_id automáticamente si no se proporciona
    employee_id = payload.employee_id
    if not employee_id:
        # Contar usuarios existentes para generar ID secuencial
        count_result = await db.execute(select(User))
        count = len(count_result.scalars().all())
        employee_id = f"EMP-{count + 1:03d}"

    # Verificar que email y employee_id no existan
    existing = await db.execute(
        select(User).where((User.email == payload.email) | (User.employee_id == employee_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email o empleado ya existen")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        employee_id=employee_id,
        role_id=payload.role_id,
        department_id=payload.department_id,
        shift_id=payload.shift_id,
        notification_preferences=payload.notification_preferences,
    )
    db.add(user)
    await db.flush()

    # Generar código de barras automáticamente
    barcode_record = QRCode(
        user_id=user.id,
        code_data=barcode.generate_code_data(user.employee_id),
        expires_at=barcode.default_expiration(),
        is_active=True
    )
    db.add(barcode_record)
    await db.commit()

    # Recargar con relaciones
    result = await db.execute(
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.role),
            selectinload(User.department),
            selectinload(User.shift)
        )
    )
    return result.scalar_one()


@router.patch("/users/{user_id}", response_model=schemas.UserOut)
async def update_user(user_id: uuid.UUID, payload: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()

    # Recargar con relaciones
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.role),
            selectinload(User.department),
            selectinload(User.shift)
        )
    )
    return result.scalar_one()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"detail": "deleted"}


@router.get("/roles", response_model=list[schemas.RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.post("/roles", response_model=schemas.RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(payload: schemas.RoleCreate, db: AsyncSession = Depends(get_db)):
    role = Role(**payload.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/departments", response_model=list[schemas.DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department))
    return result.scalars().all()


@router.post("/departments", response_model=schemas.DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(payload: schemas.DepartmentCreate, db: AsyncSession = Depends(get_db)):
    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/shifts", response_model=list[schemas.ShiftOut])
async def list_shifts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shift))
    return result.scalars().all()


@router.post("/shifts", response_model=schemas.ShiftOut, status_code=status.HTTP_201_CREATED)
async def create_shift(payload: schemas.ShiftCreate, db: AsyncSession = Depends(get_db)):
    shift = Shift(**payload.model_dump())
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return shift

