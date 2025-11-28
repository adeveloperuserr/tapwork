# tapwork

FastAPI + PostgreSQL starter for user registration, email verification, barcode-based attendance, reporting, and optional biometrics.

## ✨ Features

- 🔐 **Seguridad robusta**: JWT auth, validación de contraseñas, rate limiting, CORS configurable
- 👥 **Gestión de usuarios**: Registro, verificación de email, recuperación de contraseña
- 📊 **Control de asistencia**: Check-in/out con códigos QR, estado (a tiempo/tarde), reportes
- 🏢 **Administración**: Roles, departamentos, turnos, permisos
- 📧 **Notificaciones**: Emails automáticos para registro, asistencia y recuperación
- 🔍 **Auditoría**: Logs completos con IP, usuario, acción y cambios
- 📱 **Scanner web**: Interfaz HTML simple para escanear QR con webcam

## Stack
- FastAPI with JWT auth and role-based guards
- PostgreSQL (async SQLAlchemy 2.x) + Alembic migrations
- Mailhog (local SMTP) for notifications
- QR generation with `qrcode`
- Rate limiting with `slowapi`
- Simple web scanner (`frontend/scan.html`) using webcam + jsQR

## Quick start
```bash
cp .env.example .env
docker compose up --build
```
- API: `http://localhost:8000` (docs at `/docs`)
- Mailhog UI: `http://localhost:8025` (captures outbound mail)
- Postgres: `localhost:5432` (`tapwork` / `tapwork`)

Seed default roles and an admin user:
```bash
docker compose exec api python scripts/seed.py
```

## Key endpoints
- `POST /api/auth/register` – register + QR issuance + verification email
- `POST /api/auth/login` – JWT access token
- `POST /api/auth/verify-email` – confirm email token
- `POST /api/auth/password-reset` + `/password-reset/confirm`
- `GET /api/barcodes/me.png` – QR PNG for current user
- `POST /api/attendance/scan` – check-in/out via QR data
- `GET /api/reports/summary`, `POST /api/reports/export` – CSV/PDF
- `POST /api/biometric/enroll` – optional hashed biometric storage
- Admin-only (role `Admin`): `/api/admin/*` for users, roles, departments, shifts

Open the scanner UI locally at `frontend/scan.html` (served via a simple file server or your browser) and point it to the API base URL.

## Migrations
```bash
alembic upgrade head          # apply
alembic revision -m "msg"     # create new revision
```
Alembic reads connection info from `.env` via `app.config.Settings`.

## Environment notes
- Outbound email uses SMTP settings in `.env` (defaults to Mailhog).
- Biometric features only store a provided hash/template (Base64); matching is out of scope and should be implemented by an external verifier.
- The app creates tables on startup for convenience; prefer Alembic in real deployments.

## 🔒 Seguridad

### Validación de contraseñas
Las contraseñas deben cumplir:
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos una minúscula
- Al menos un número

### Rate Limiting
Protección contra fuerza bruta:
- Registro: 5 intentos/minuto
- Login: 10 intentos/minuto
- Reset password: 3 intentos/minuto

### CORS Configurable
Configura `ALLOWED_ORIGINS` en `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:3000,https://miapp.com
```

### SECRET_KEY
⚠️ **IMPORTANTE**: Genera una clave segura para producción:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

## 🚀 Despliegue en Hosting Gratuito

Ver **[DEPLOYMENT.md](DEPLOYMENT.md)** para guías detalladas de despliegue en:
- Railway (recomendado)
- Render
- Fly.io

## 📝 Credenciales por Defecto

Después de ejecutar `seed.py`:
```
Email: admin@example.com
Password: Admin123!
```

⚠️ **Cambia las credenciales en producción** configurando `ADMIN_EMAIL` y `ADMIN_PASSWORD` en `.env`

## What's included
- ✅ Registro y autenticación con JWT
- ✅ Verificación de email
- ✅ Recuperación de contraseña
- ✅ Validación robusta de contraseñas
- ✅ Rate limiting anti fuerza bruta
- ✅ Control de asistencia con QR (check-in/out)
- ✅ Notificaciones por email (con opt-out)
- ✅ Gestión admin (usuarios, roles, departamentos, turnos)
- ✅ Reportes (CSV/PDF)
- ✅ Paginación en endpoints
- ✅ Audit logs con IP
- ✅ CORS configurable
- ✅ Almacenamiento biométrico opcional
- ✅ Scanner web UI

## Pendiente
- Production-grade RBAC policies
- Biometric matching implementation
- Audit log viewer UI
- Tests (unit + e2e)
- Redis caching
