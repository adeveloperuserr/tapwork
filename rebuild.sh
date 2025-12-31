#!/bin/bash
set -e

# Verificar que docker compose esté disponible
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado o no está en el PATH"
    echo "Asegúrate de que Docker Desktop esté corriendo"
    exit 1
fi

echo "Descargando ultimos cambios de Git..."
if ! git pull; then
    echo "⚠️  git pull falló. Intentando sync completo..."

    # Guardar cambios locales si los hay
    git stash save "Auto-stash antes de sync - $(date)" || true

    # Obtener la rama actual
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

    # Hacer fetch y reset
    echo "Haciendo fetch del remote..."
    git fetch origin

    echo "Reseteando a origin/$CURRENT_BRANCH..."
    git reset --hard origin/$CURRENT_BRANCH

    echo "✅ Sync completado exitosamente"

    # Aplicar stash si había cambios guardados
    if git stash list | grep -q "Auto-stash antes de sync"; then
        echo "Reaplicando cambios locales guardados..."
        git stash pop || echo "⚠️  No se pudieron reaplicar los cambios locales"
    fi
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
