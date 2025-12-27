#!/bin/bash
set -e

# Verificar que docker compose esté disponible
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado o no está en el PATH"
    echo "Asegúrate de que Docker Desktop esté corriendo"
    exit 1
fi

echo "Descargando ultimos cambios de Git..."
git pull || {
    echo "Advertencia: git pull fallo. Continuando con rebuild..."
}

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
