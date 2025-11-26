# tapwork

FastAPI + PostgreSQL starter for user registration, email verification, barcode-based attendance, reporting, and optional biometrics.

## Stack
- FastAPI with JWT auth and role-based guards
- PostgreSQL (async SQLAlchemy 2.x) + Alembic migrations
- Mailhog (local SMTP) for notifications
- QR generation with `qrcode`
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

## What’s included / pending
- Included: registration, email verification, password resets, attendance check-in/out by QR, notifications (registration/reset/attendance with opt-out flags), admin management, reports (CSV/PDF), optional biometric storage, web scanner UI.
- Pending: production-grade RBAC policies, biometric matching, rate limiting, audit log viewer UI, and e2e tests. Let me know if you want these added next.
