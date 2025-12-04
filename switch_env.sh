#!/bin/bash
# Script para alternar entre ambiente de desenvolvimento e produção

if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    echo "Configurando para PRODUÇÃO..."
    sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=http://3.236.36.55:8000|g' .env
    echo "FRONTEND_URL definido para: http://3.236.36.55:8000"
elif [ "$1" = "dev" ] || [ "$1" = "development" ]; then
    echo "Configurando para DESENVOLVIMENTO..."
    sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=http://localhost:8000|g' .env
    echo "FRONTEND_URL definido para: http://localhost:8000"
else
    echo "Uso: $0 [dev|prod]"
    echo ""
    echo "Exemplos:"
    echo "  $0 dev   # Configura para desenvolvimento (localhost)"
    echo "  $0 prod  # Configura para produção (AWS)"
    echo ""
    echo "URL atual:"
    grep "FRONTEND_URL" .env
fi