#!/bin/bash
set -e  # Detener si hay errores

# Verificar que docker compose esté disponible
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado o no está en el PATH"
    echo "   Asegúrate de que Docker Desktop esté corriendo"
    exit 1
fi

echo "🔄 Deteniendo contenedores de Docker..."
docker compose down || true  # No fallar si no hay contenedores corriendo

echo ""
echo "🔨 Reconstruyendo y levantando contenedores..."
docker compose up --build -d

echo ""
echo "✅ ¡Listo! Los contenedores están corriendo."
echo ""
echo "📋 Comandos útiles:"
echo "   - Ver logs en vivo:  docker compose logs -f"
echo "   - Ver logs de API:   docker compose logs -f api"
echo "   - Ver estado:        docker compose ps"
