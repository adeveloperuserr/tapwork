import asyncio
import uuid
import os

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Role, User, QRCode
from app.utils.security import hash_password
from app.utils import barcode


async def seed():
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)

    async with SessionLocal() as session:
        default_roles = [
            ("Employee", "Registro básico", {"attendance": ["read", "create"]}),
            ("Supervisor", "Supervisa equipos", {"attendance": ["read"], "reports": ["read"]}),
            ("HR Manager", "Recursos humanos", {"attendance": ["read"], "reports": ["read", "generate"], "users": ["manage"]}),
            ("Admin", "Acceso completo", {"attendance": ["*"], "reports": ["*"], "users": ["*"], "settings": ["*"]}),
        ]
        for name, description, permissions in default_roles:
            existing = await session.scalar(select(Role).where(Role.name == name))
            if not existing:
                session.add(Role(name=name, description=description, permissions=permissions))
        await session.commit()

        admin_email = os.getenv("ADMIN_EMAIL", "adeveloper.user@gmail.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "aDeveloperUser2025$")  # Contraseña por defecto con validación
        existing_admin = await session.scalar(select(User).where(User.email == admin_email))
        if not existing_admin:
            admin_role = await session.scalar(select(Role).where(Role.name == "Admin"))
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                first_name="Admin",
                last_name="User",
                employee_id="ADM-001",
                role=admin_role,
                is_active=True,
                is_email_verified=True,
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            # Generar código de barras para el admin usando su employee_id
            barcode_record = QRCode(
                user_id=admin_user.id,
                code_data=barcode.generate_code_data(admin_user.employee_id),
                expires_at=barcode.default_expiration(),
                is_active=True
            )
            session.add(barcode_record)
            await session.commit()

            print(f"✓ Usuario admin creado: {admin_email}")
            print(f"✓ Código de barras generado para admin (ID: {admin_user.employee_id})")
            if admin_password == "aDeveloperUser2025$":
                print("⚠️  ADVERTENCIA: Usando contraseña por defecto. Configura ADMIN_PASSWORD en .env para producción")
        else:
            # Si el admin ya existe, verificar si tiene código de barras
            existing_barcode = await session.scalar(select(QRCode).where(QRCode.user_id == existing_admin.id))
            if not existing_barcode:
                barcode_record = QRCode(
                    user_id=existing_admin.id,
                    code_data=barcode.generate_code_data(existing_admin.employee_id),
                    expires_at=barcode.default_expiration(),
                    is_active=True
                )
                session.add(barcode_record)
                await session.commit()
                print(f"✓ Código de barras generado para admin existente: {admin_email} (ID: {existing_admin.employee_id})")


if __name__ == "__main__":
    asyncio.run(seed())

