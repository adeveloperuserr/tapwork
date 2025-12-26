import asyncio
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.utils.security import hash_password


async def update_admin():
    """Actualiza el usuario admin con las credenciales correctas"""
    async with SessionLocal() as session:
        # Buscar admin por employee_id
        admin = await session.scalar(
            select(User).where(User.employee_id == "ADM-001")
        )

        if not admin:
            print("❌ No se encontró usuario con employee_id='ADM-001'")
            return

        print(f"📝 Usuario encontrado: {admin.email}")

        # Actualizar credenciales
        admin.email = "admin@tapwork.com"
        admin.password_hash = hash_password("Admin123!")
        admin.first_name = "Administrador"
        admin.last_name = "Sistema"
        admin.is_active = True
        admin.is_email_verified = True

        await session.commit()

        print("\n✅ Usuario admin actualizado exitosamente")
        print("=" * 60)
        print("🔑 CREDENCIALES DE ACCESO")
        print("=" * 60)
        print("URL:      http://localhost:8000/admin/login.html")
        print("Email:    admin@tapwork.com")
        print("Password: Admin123!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(update_admin())
