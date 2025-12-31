#!/bin/bash
set -e

# Verificar que docker compose esté disponible
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado o no está en el PATH"
    echo "Asegúrate de que Docker Desktop esté corriendo"
    exit 1
fi

echo "Descargando ultimos cambios de Git..."

# Verificar si hay cambios locales
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  ADVERTENCIA: Tienes cambios locales no commiteados"
    echo "   Estos cambios se DESCARTARÁN para sincronizar con el servidor"
    echo ""
fi

# Obtener la rama actual
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Hacer fetch
echo "Haciendo fetch del remote..."
git fetch origin

# Verificar si estamos desactualizados
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$CURRENT_BRANCH)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "Sincronizando con origin/$CURRENT_BRANCH..."

    # Descartar cambios locales y sincronizar
    git reset --hard origin/$CURRENT_BRANCH
    git clean -fd  # Limpiar archivos no trackeados

    echo "✅ Sync completado exitosamente"
else
    echo "✅ Ya estás actualizado con origin/$CURRENT_BRANCH"
fi

echo ""
echo "Deteniendo contenedores de Docker..."
docker compose down || true

echo ""
echo "Reconstruyendo y levantando contenedores..."
docker compose up --build -d

echo ""
echo "Listo! Los contenedores están corriendo."
echo ""
echo "Comandos utiles:"
echo "  - Ver logs en vivo:  docker compose logs -f"
echo "  - Ver logs de API:   docker compose logs -f api"
echo "  - Ver estado:        docker compose ps"
