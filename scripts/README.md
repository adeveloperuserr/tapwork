# 🌱 Script de Seed - Inicialización del Sistema

## 📋 ¿Qué hace este script?

El script `seed.py` inicializa la base de datos con datos esenciales para empezar a usar el sistema:

1. **Roles por defecto**:
   - Employee (Empleado básico)
   - Supervisor
   - HR Manager (Gerente de RRHH)
   - **Admin** (Acceso completo)

2. **Departamentos**:
   - Administración
   - Recursos Humanos
   - Tecnología
   - Operaciones

3. **Turnos**:
   - Administrativo (8:00-17:00, Lun-Vie)
   - Matutino (6:00-14:00, Lun-Sab)
   - Vespertino (14:00-22:00, Lun-Sab)
   - Nocturno (22:00-6:00, Todos los días)

4. **Usuario Administrador**:
   - Email: `admin@tapwork.com`
   - Password: `Admin123!`
   - ID Empleado: `ADM-001`
   - Con código de barras generado automáticamente

## 🚀 Cómo Ejecutar

### Opción 1: Desde Docker (Recomendado)

```bash
# Ejecutar seed dentro del contenedor
docker compose exec api python scripts/seed.py
```

### Opción 2: Directamente (si tienes Python local)

```bash
# Activar entorno virtual si lo usas
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Ejecutar script
python scripts/seed.py
```

## 🔧 Configuración Personalizada

Puedes personalizar las credenciales del admin usando variables de entorno:

### Crear archivo `.env`:

```bash
ADMIN_EMAIL=tu-email@empresa.com
ADMIN_PASSWORD=TuContraseñaSegura123!
```

### O usar variables de entorno directamente:

```bash
# Linux/Mac
export ADMIN_EMAIL=tu-email@empresa.com
export ADMIN_PASSWORD=TuContraseñaSegura123!
docker compose exec api python scripts/seed.py

# Windows PowerShell
$env:ADMIN_EMAIL="tu-email@empresa.com"
$env:ADMIN_PASSWORD="TuContraseñaSegura123!"
docker compose exec api python scripts/seed.py
```

## ✅ Verificación

Después de ejecutar el seed, deberías ver algo como:

```
🌱 Iniciando seed de datos...

📋 Creando roles...
  ✓ Rol creado: Employee
  ✓ Rol creado: Supervisor
  ✓ Rol creado: HR Manager
  ✓ Rol creado: Admin

🏢 Creando departamentos...
  ✓ Departamento creado: Administración
  ✓ Departamento creado: Recursos Humanos
  ✓ Departamento creado: Tecnología
  ✓ Departamento creado: Operaciones

⏰ Creando turnos...
  ✓ Turno creado: Administrativo (08:00-17:00)
  ✓ Turno creado: Matutino (06:00-14:00)
  ✓ Turno creado: Vespertino (14:00-22:00)
  ✓ Turno creado: Nocturno (22:00-06:00)

👤 Creando usuario administrador...
  ✓ Usuario admin creado: admin@tapwork.com
  ✓ ID Empleado: ADM-001
  ✓ Departamento: Administración
  ✓ Turno: Administrativo
  ✓ Código de barras generado

============================================================
🔑 CREDENCIALES DE ACCESO AL PANEL
============================================================
URL:      http://localhost:8000/admin/login.html
Email:    admin@tapwork.com
Password: Admin123!
============================================================

⚠️  ADVERTENCIA: Usando contraseña por defecto.
   Para producción, configura ADMIN_PASSWORD en .env

✅ Seed completado exitosamente
```

## 🔐 Acceder al Panel de Administrador

1. Abre tu navegador en: `http://localhost:8000/admin/login.html`
2. Ingresa las credenciales:
   - **Email**: `admin@tapwork.com`
   - **Password**: `Admin123!`
3. ¡Listo! Ya puedes administrar usuarios, departamentos y turnos.

## 🔄 Ejecución Múltiple (Idempotencia)

El script es **idempotente**, lo que significa que:

- ✅ Puedes ejecutarlo múltiples veces sin problemas
- ✅ Si los datos ya existen, los omite
- ✅ Solo crea lo que falta

Ejemplo de segunda ejecución:

```
📋 Creando roles...
  ⊙ Rol ya existe: Employee
  ⊙ Rol ya existe: Supervisor
  ⊙ Rol ya existe: HR Manager
  ⊙ Rol ya existe: Admin

👤 Creando usuario administrador...
  ⊙ Usuario admin ya existe: admin@tapwork.com
```

## ⚠️ Seguridad en Producción

**IMPORTANTE**: Para entornos de producción:

1. ❌ **NUNCA** uses la contraseña por defecto `Admin123!`
2. ✅ Configura `ADMIN_PASSWORD` en `.env` con una contraseña fuerte
3. ✅ Cambia la contraseña del admin inmediatamente después del primer login
4. ✅ Considera usar variables de entorno del servidor en lugar de `.env`

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'app'"

Asegúrate de estar ejecutando el script desde el contenedor Docker o con el entorno virtual activado.

### Error: "sqlalchemy.exc.OperationalError: could not connect to server"

Verifica que:
1. Docker Compose esté corriendo: `docker compose ps`
2. La base de datos esté levantada: `docker compose logs db`
3. Las credenciales en `.env` sean correctas

### El admin ya existe pero no puedo hacer login

Si olvidaste la contraseña, puedes:

1. Eliminar el usuario admin de la base de datos
2. Volver a ejecutar el seed con la nueva contraseña configurada

```sql
-- Conectar a la base de datos
docker compose exec db psql -U postgres -d tapwork_db

-- Eliminar usuario admin
DELETE FROM users WHERE email = 'admin@tapwork.com';

-- Salir
\q
```

Luego ejecutar el seed nuevamente.

## 📚 Siguientes Pasos

Después de ejecutar el seed:

1. Accede al panel de admin
2. Crea más departamentos si los necesitas
3. Configura turnos adicionales
4. Crea usuarios desde el panel (no necesitas la API directamente)
5. Genera códigos de barras para los empleados
6. Prueba el terminal de asistencia en `/scan.html`
