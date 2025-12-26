import asyncio
import uuid
import os
from datetime import time

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Department, Role, Shift, User, QRCode
from app.utils.security import hash_password
from app.utils import barcode


async def seed():
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)

    async with SessionLocal() as session:
        print("🌱 Iniciando seed de datos...")
        print()

        # ============================================
        # 1. CREAR ROLES POR DEFECTO
        # ============================================
        print("📋 Creando roles...")
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
                print(f"  ✓ Rol creado: {name}")
            else:
                print(f"  ⊙ Rol ya existe: {name}")
        await session.commit()
        print()

        # ============================================
        # 2. CREAR DEPARTAMENTOS POR DEFECTO
        # ============================================
        print("🏢 Creando departamentos...")
        default_departments = [
            ("Administración", "Departamento administrativo general"),
            ("Recursos Humanos", "Gestión de personal y talento"),
            ("Tecnología", "Desarrollo y sistemas"),
            ("Operaciones", "Operaciones y logística"),
        ]
        for name, description in default_departments:
            existing = await session.scalar(select(Department).where(Department.name == name))
            if not existing:
                session.add(Department(name=name, description=description, manager_id=None))
                print(f"  ✓ Departamento creado: {name}")
            else:
                print(f"  ⊙ Departamento ya existe: {name}")
        await session.commit()
        print()

        # ============================================
        # 3. CREAR TURNOS POR DEFECTO
        # ============================================
        print("⏰ Creando turnos...")
        default_shifts = [
            ("Administrativo", time(8, 0), time(17, 0), 15, [1, 2, 3, 4, 5]),  # Lun-Vie 8:00-17:00
            ("Matutino", time(6, 0), time(14, 0), 10, [1, 2, 3, 4, 5, 6]),     # Lun-Sab 6:00-14:00
            ("Vespertino", time(14, 0), time(22, 0), 10, [1, 2, 3, 4, 5, 6]),  # Lun-Sab 14:00-22:00
            ("Nocturno", time(22, 0), time(6, 0), 15, [0, 1, 2, 3, 4, 5, 6]),  # Todos 22:00-6:00
        ]
        for name, start, end, grace, working_days in default_shifts:
            existing = await session.scalar(select(Shift).where(Shift.name == name))
            if not existing:
                session.add(Shift(
                    name=name,
                    start_time=start,
                    end_time=end,
                    grace_period_minutes=grace,
                    working_days=working_days
                ))
                print(f"  ✓ Turno creado: {name} ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})")
            else:
                print(f"  ⊙ Turno ya existe: {name}")
        await session.commit()
        print()

        # ============================================
        # 4. CREAR USUARIO ADMINISTRADOR
        # ============================================
        print("👤 Creando usuario administrador...")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@tapwork.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
        admin_employee_id = "ADM-001"

        # Verificar por email O por employee_id
        existing_admin = await session.scalar(
            select(User).where(
                (User.email == admin_email) | (User.employee_id == admin_employee_id)
            )
        )

        if not existing_admin:
            # Obtener IDs necesarios
            admin_role = await session.scalar(select(Role).where(Role.name == "Admin"))
            admin_dept = await session.scalar(select(Department).where(Department.name == "Administración"))
            admin_shift = await session.scalar(select(Shift).where(Shift.name == "Administrativo"))

            # Crear usuario admin
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                first_name="Administrador",
                last_name="Sistema",
                employee_id=admin_employee_id,
                role=admin_role,
                department=admin_dept,
                shift=admin_shift,
                is_active=True,
                is_email_verified=True,
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            # Generar código de barras para el admin
            barcode_record = QRCode(
                user_id=admin_user.id,
                code_data=barcode.generate_code_data(admin_user.employee_id),
                expires_at=barcode.default_expiration(),
                is_active=True
            )
            session.add(barcode_record)
            await session.commit()

            print(f"  ✓ Usuario admin creado: {admin_email}")
            print(f"  ✓ ID Empleado: {admin_user.employee_id}")
            print(f"  ✓ Departamento: {admin_dept.name if admin_dept else 'N/A'}")
            print(f"  ✓ Turno: {admin_shift.name if admin_shift else 'N/A'}")
            print(f"  ✓ Código de barras generado")
            print()
            print("=" * 60)
            print("🔑 CREDENCIALES DE ACCESO AL PANEL")
            print("=" * 60)
            print(f"URL:      http://localhost:8000/admin/login.html")
            print(f"Email:    {admin_email}")
            print(f"Password: {admin_password}")
            print("=" * 60)
            print()
            if admin_password == "Admin123!":
                print("⚠️  ADVERTENCIA: Usando contraseña por defecto.")
                print("   Para producción, configura ADMIN_PASSWORD en .env")
        else:
            print(f"  ⊙ Usuario admin ya existe: {admin_email}")

            # Verificar si tiene código de barras
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
                print(f"  ✓ Código de barras generado para admin existente")

            print()
            print("=" * 60)
            print("🔑 CREDENCIALES DE ACCESO AL PANEL")
            print("=" * 60)
            print(f"URL:      http://localhost:8000/admin/login.html")
            print(f"Email:    {admin_email}")
            print(f"Password: (usar contraseña configurada)")
            print("=" * 60)

        print()
        print("✅ Seed completado exitosamente")


if __name__ == "__main__":
    asyncio.run(seed())

