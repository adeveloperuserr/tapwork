import asyncio
import uuid
import os

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Role, User
from app.utils.security import hash_password


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

        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")  # Contraseña por defecto con validación
        existing_admin = await session.scalar(select(User).where(User.email == admin_email))
        if not existing_admin:
            admin_role = await session.scalar(select(Role).where(Role.name == "Admin"))
            session.add(
                User(
                    email=admin_email,
                    password_hash=hash_password(admin_password),
                    first_name="Admin",
                    last_name="User",
                    employee_id="ADM-001",
                    role=admin_role,
                    is_active=True,
                    is_email_verified=True,
                )
            )
            await session.commit()
            print(f"✓ Usuario admin creado: {admin_email}")
            if admin_password == "Admin123!":
                print("⚠️  ADVERTENCIA: Usando contraseña por defecto. Configura ADMIN_PASSWORD en .env para producción")


if __name__ == "__main__":
    asyncio.run(seed())

