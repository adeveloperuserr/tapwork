# Guía de Despliegue - Tapwork

Esta guía explica cómo desplegar Tapwork en diferentes plataformas de hosting gratuito.

## 📋 Requisitos Previos

- Cuenta en la plataforma de hosting elegida
- Base de datos PostgreSQL (la mayoría de plataformas ofrecen PostgreSQL gratuito)
- Cuenta de correo SMTP (puedes usar Gmail, SendGrid, etc.)

## 🚀 Despliegue en Railway

Railway ofrece un tier gratuito generoso y es muy fácil de configurar.

### Pasos:

1. **Crear cuenta en Railway**: https://railway.app

2. **Crear nuevo proyecto**:
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio de GitHub

3. **Agregar PostgreSQL**:
   - En tu proyecto, haz clic en "+ New"
   - Selecciona "Database" → "PostgreSQL"
   - Railway generará automáticamente la variable `DATABASE_URL`

4. **Configurar variables de entorno**:
   - Ve a tu servicio → "Variables"
   - Añade las siguientes variables:

   ```bash
   # Genera una SECRET_KEY segura
   SECRET_KEY=<genera-una-clave-con-python-secrets>
   ENVIRONMENT=production

   # CORS (tu dominio de Railway)
   ALLOWED_ORIGINS=https://tu-app.up.railway.app

   # SMTP (ejemplo con Gmail)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_TLS=true
   SMTP_USERNAME=tu-email@gmail.com
   SMTP_PASSWORD=tu-app-password
   MAIL_FROM=tu-email@gmail.com

   # URLs
   FRONTEND_BASE_URL=https://tu-frontend.com
   API_BASE_URL=https://tu-app.up.railway.app

   # Admin
   ADMIN_EMAIL=admin@tudominio.com
   ADMIN_PASSWORD=<contraseña-segura>
   ```

5. **Generar SECRET_KEY segura**:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

6. **Ejecutar migraciones y seed**:
   - Una vez desplegado, ve a "Settings" → "Deploy"
   - Ejecuta el comando de seed:
   ```bash
   python scripts/seed.py
   ```

7. **¡Listo!** Tu API estará disponible en `https://tu-app.up.railway.app`

---

## 🌐 Despliegue en Render

Render también ofrece un tier gratuito para aplicaciones web y bases de datos.

### Pasos:

1. **Crear cuenta en Render**: https://render.com

2. **Crear PostgreSQL Database**:
   - Dashboard → "+ New" → "PostgreSQL"
   - Nombre: `tapwork-db`
   - Plan: Free
   - Copia la "Internal Database URL"

3. **Crear Web Service**:
   - Dashboard → "+ New" → "Web Service"
   - Conecta tu repositorio de GitHub
   - Configuración:
     - **Name**: `tapwork-api`
     - **Environment**: `Docker`
     - **Plan**: Free

4. **Configurar variables de entorno** (igual que Railway):
   - Ve a "Environment" y añade las variables necesarias
   - Usa la `DATABASE_URL` interna de PostgreSQL

5. **Ejecutar seed**:
   - Conecta por SSH o usa el shell de Render:
   ```bash
   python scripts/seed.py
   ```

---

## ☁️ Despliegue en Fly.io

Fly.io es ideal para aplicaciones Docker.

### Pasos:

1. **Instalar flyctl**:
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login**:
   ```bash
   flyctl auth login
   ```

3. **Crear app**:
   ```bash
   flyctl launch
   # Responde las preguntas (elige tu región, etc.)
   ```

4. **Crear PostgreSQL**:
   ```bash
   flyctl postgres create
   # Elige un nombre: tapwork-db
   ```

5. **Conectar PostgreSQL a la app**:
   ```bash
   flyctl postgres attach tapwork-db
   ```

6. **Configurar variables de entorno**:
   ```bash
   flyctl secrets set SECRET_KEY="<tu-clave-segura>"
   flyctl secrets set ENVIRONMENT="production"
   flyctl secrets set ALLOWED_ORIGINS="https://tu-app.fly.dev"
   flyctl secrets set ADMIN_EMAIL="admin@tudominio.com"
   flyctl secrets set ADMIN_PASSWORD="<contraseña-segura>"
   # ... etc
   ```

7. **Desplegar**:
   ```bash
   flyctl deploy
   ```

8. **Ejecutar seed**:
   ```bash
   flyctl ssh console
   python scripts/seed.py
   ```

---

## 🔐 Seguridad en Producción

### Variables de entorno obligatorias:

1. **SECRET_KEY**: Genera una única y segura
2. **ENVIRONMENT**: Establece en `production`
3. **ALLOWED_ORIGINS**: Lista específica de dominios (NO uses `*`)
4. **ADMIN_PASSWORD**: Contraseña fuerte (mínimo 8 caracteres, mayúsculas, minúsculas, números)

### SMTP Recomendado:

**Para producción, usa un servicio profesional**:
- **SendGrid**: 100 emails/día gratis
- **Mailgun**: 5,000 emails/mes gratis
- **AWS SES**: Muy económico
- **Gmail**: Solo para pruebas (16 emails/día con contraseña de aplicación)

### Configuración Gmail (solo desarrollo):
1. Habilita verificación en 2 pasos
2. Genera "Contraseña de aplicación": https://myaccount.google.com/apppasswords
3. Usa esa contraseña en `SMTP_PASSWORD`

---

## 📊 Monitoreo

### Logs en Railway:
```bash
# Ver logs en tiempo real
railway logs
```

### Logs en Render:
- Ve a tu servicio → "Logs" en el dashboard

### Logs en Fly.io:
```bash
flyctl logs
```

---

## 🔄 Actualizar el Despliegue

### Railway y Render:
- Automático al hacer push a GitHub (si está configurado)

### Fly.io:
```bash
flyctl deploy
```

---

## 🆘 Troubleshooting

### Error: "SECRET_KEY debe ser configurada en producción"
- Asegúrate de haber configurado `SECRET_KEY` en las variables de entorno
- Genera una nueva: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`

### Error de conexión a base de datos:
- Verifica que `DATABASE_URL` esté correctamente configurada
- Asegúrate de usar el formato correcto: `postgresql+asyncpg://user:pass@host:port/db`

### Rate limiting muy agresivo:
- Ajusta los límites en `app/routes/auth.py`:
  - `@limiter.limit("5/minute")` → aumenta el número según necesites

### CORS bloqueado:
- Verifica `ALLOWED_ORIGINS` incluya tu dominio frontend
- Formato: `https://app.com,https://www.app.com` (sin espacios)

---

## 💡 Optimizaciones para Producción

1. **Habilitar compresión**:
   ```python
   # En app/main.py
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

2. **Configurar workers de Uvicorn**:
   ```dockerfile
   # En Dockerfile, cambiar CMD
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

3. **Usar CDN para assets estáticos** (frontend/scan.html)

4. **Implementar caché** con Redis (disponible gratis en Railway/Render)

---

## 📚 Recursos Adicionales

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
