# 🚀 Guía Rápida de Inicio - Tapwork

## 1️⃣ Requisitos Previos

### Instalar Docker Desktop
- **Windows/Mac**: https://www.docker.com/products/docker-desktop/
- **Linux**:
  ```bash
  sudo apt-get install docker.io docker-compose
  ```

Verificar instalación:
```bash
docker --version
docker compose version
```

---

## 2️⃣ Configuración Inicial

### Paso 1: Crear archivo de configuración
```bash
cp .env.example .env
```

### Paso 2: (Opcional) Personalizar configuración
Edita `.env` si quieres cambiar algo. Por defecto está listo para funcionar.

---

## 3️⃣ Levantar el Proyecto

### Iniciar todos los servicios
```bash
docker compose up --build
```

**Primera vez**: Puede tardar 2-3 minutos descargando imágenes.

**Verás estos mensajes cuando esté listo:**
```
tapwork-api-1     | INFO:     Application startup complete.
tapwork-api-1     | INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 4️⃣ Crear Usuario Administrador

**En otra terminal**, ejecuta:
```bash
docker compose exec api python scripts/seed.py
```

**Credenciales creadas:**
- Email: `adeveloper.user@gmail.com`
- Password: `Admin123!`

---

## 5️⃣ Verificar que Funciona

### ✅ Health Check
Abre en tu navegador: **http://localhost:8000/health**

Deberías ver:
```json
{"status": "ok", "env": "development"}
```

### 📚 Documentación Interactiva (Swagger)
**http://localhost:8000/docs**

### 📧 Mailhog (ver emails enviados)
**http://localhost:8025**

### 🗄️ PostgreSQL
- Host: `localhost`
- Puerto: `5432`
- Usuario: `tapwork`
- Password: `tapwork`
- Database: `tapwork`

---

## 6️⃣ Probar la API

### Opción A: Desde Swagger (más fácil)

1. Ve a **http://localhost:8000/docs**
2. Busca `POST /api/auth/login`
3. Haz clic en "Try it out"
4. Ingresa:
   ```json
   {
     "email": "adeveloper.user@gmail.com",
     "password": "Admin123!"
   }
   ```
5. Haz clic en "Execute"
6. **Copia el `access_token`** de la respuesta

7. Haz clic en el botón **"Authorize"** (arriba a la derecha, icono de candado 🔒)
8. Pega el token en el campo "Value": `<tu-token-aquí>`
9. Haz clic en "Authorize" y luego "Close"

✅ **Ahora puedes probar todos los endpoints protegidos**

---

### Opción B: Desde la terminal (curl)

#### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "adeveloper.user@gmail.com",
    "password": "Admin123!"
  }'
```

**Guarda el token de la respuesta**

#### 2. Ver tu perfil
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TU-TOKEN-AQUÍ>"
```

#### 3. Registrar un nuevo usuario
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "Password123",
    "first_name": "Juan",
    "last_name": "Pérez",
    "employee_id": "EMP-001"
  }'
```

---

## 7️⃣ Usar el Scanner de QR

### Paso 1: Obtener tu código QR

1. Inicia sesión en Swagger (paso anterior)
2. Ve a `GET /api/barcodes/me.png`
3. Haz clic en "Try it out" → "Execute"
4. Verás tu código QR (guárdalo o imprímelo)

### Paso 2: Abrir el Scanner

Abre en tu navegador:
**file:///ruta/a/tapwork/frontend/scan.html**

O levanta un servidor simple:
```bash
cd frontend
python -m http.server 3000
```

Luego abre: **http://localhost:3000/scan.html**

### Paso 3: Configurar la API URL

En el scanner, ingresa:
```
http://localhost:8000
```

### Paso 4: Permitir acceso a la cámara

El navegador te pedirá permiso. Acepta.

### Paso 5: Escanear QR

Apunta tu código QR a la cámara. ¡Verás el check-in registrado!

---

## 8️⃣ Ver los Emails Enviados

Los emails se capturan en **Mailhog**. Abre:

**http://localhost:8025**

Aquí verás todos los emails de:
- Verificación de cuenta
- Recuperación de contraseña
- Alertas de asistencia

---

## 🛑 Detener el Proyecto

### Detener los servicios (mantiene los datos)
```bash
docker compose down
```

### Detener y eliminar TODO (base de datos incluida)
```bash
docker compose down -v
```

---

## 🔄 Reiniciar el Proyecto

```bash
docker compose up
```

(Ya no necesitas `--build` a menos que hayas cambiado el código)

---

## 🐛 Troubleshooting

### Error: "port 8000 is already in use"
Otro servicio está usando el puerto 8000.

**Solución 1**: Detener el otro servicio

**Solución 2**: Cambiar el puerto en `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Usar puerto 8001 en lugar de 8000
```

### Error: "Cannot connect to Docker daemon"

**Windows/Mac**: Asegúrate de que Docker Desktop está corriendo

**Linux**:
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
```
Luego cierra sesión y vuelve a entrar.

### Los cambios en el código no se reflejan

Reconstruye la imagen:
```bash
docker compose up --build
```

### Ver logs de un servicio específico

```bash
# Ver logs de la API
docker compose logs api

# Ver logs en tiempo real
docker compose logs -f api
```

### Entrar a la base de datos

```bash
docker compose exec db psql -U tapwork -d tapwork
```

Una vez dentro:
```sql
-- Ver todas las tablas
\dt

-- Ver usuarios
SELECT email, first_name, last_name, is_active FROM users;

-- Salir
\q
```

---

## 📊 Comandos Útiles

### Ver servicios corriendo
```bash
docker compose ps
```

### Reiniciar un servicio específico
```bash
docker compose restart api
```

### Ver uso de recursos
```bash
docker stats
```

### Limpiar todo Docker (cuidado)
```bash
docker system prune -a
```

---

## 🎯 Siguientes Pasos

1. **Prueba todos los endpoints** en Swagger
2. **Crea un usuario de prueba** con el endpoint de registro
3. **Escanea códigos QR** con el scanner web
4. **Revisa los emails** en Mailhog
5. **Explora los reportes** en `/api/reports/summary`

---

## 📚 Recursos Adicionales

- **Documentación API**: http://localhost:8000/docs
- **Redoc (otra vista)**: http://localhost:8000/redoc
- **Mailhog**: http://localhost:8025
- **Guía de despliegue**: Ver [DEPLOYMENT.md](DEPLOYMENT.md)

---

## ⚙️ Configuración Avanzada

### Cambiar contraseña del admin antes de crear

Edita `.env` antes de ejecutar `seed.py`:
```bash
ADMIN_EMAIL=micorreo@empresa.com
ADMIN_PASSWORD=MiPassword123Seguro
```

### Usar Gmail para emails reales

Edita `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password  # No tu contraseña normal
MAIL_FROM=tu-email@gmail.com
```

**Obtener App Password**: https://myaccount.google.com/apppasswords

### Generar SECRET_KEY segura

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Copia el resultado y pégalo en `.env`:
```bash
SECRET_KEY=tu-clave-generada-aquí
```

---

## 💡 Tips

- **Desarrollo**: Deja `docker compose up` corriendo y los cambios se recargan automáticamente
- **Logs**: Usa `docker compose logs -f` para ver qué está pasando
- **Base de datos**: Los datos persisten entre reinicios (a menos que uses `-v`)
- **Emails**: Todos se capturan en Mailhog, no se envían realmente

---

¡Listo! 🎉 Ahora tienes Tapwork corriendo localmente.
