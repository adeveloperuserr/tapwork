#!/bin/bash

echo "🔄 Deteniendo contenedores de Docker..."
docker compose down

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
