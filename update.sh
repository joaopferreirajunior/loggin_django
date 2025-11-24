#!/bin/bash
# ============================
# update.sh - Auto Deploy Django + Docker (branch dev, usando RDS)
# ============================

PROJECT_DIR="/home/ubuntu/loggin_django"
LOG_FILE="$PROJECT_DIR/update_aws.log"
BRANCH="dev"
DJANGO_SERVICE="django"   # nome do serviço do Django no docker-compose.yml

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR" || {
    log "ERRO: diretório $PROJECT_DIR não encontrado."
    exit 1
}

# Verifica dependências básicas
if ! command -v git &> /dev/null; then
    log "ERRO: git não encontrado."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log "ERRO: docker não encontrado."
    exit 1
fi

# Detectar docker compose vs docker-compose
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DC="docker-compose"
else
    log "ERRO: nem 'docker compose' nem 'docker-compose' encontrados."
    exit 1
fi

log "==== Iniciando verificação de atualização (branch: $BRANCH) ===="
log "Usando comando Docker Compose: $DC"

# Buscar atualizações do repositório remoto
log "Buscando atualizações da branch '$BRANCH'..."
if ! git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
    log "ERRO: falha ao buscar atualizações do repositório (veja detalhes no log)."
    exit 1
fi

OLD_HASH=$(git rev-parse HEAD)
NEW_HASH=$(git rev-parse "origin/$BRANCH")

log "Hash atual:  $OLD_HASH"
log "Hash remoto: $NEW_HASH"

# Se houver atualização
if [ "$OLD_HASH" != "$NEW_HASH" ]; then
    log "🚀 Atualização detectada — iniciando deploy..."

    # Garante limpeza total do repositório local
    git reset --hard HEAD >> "$LOG_FILE" 2>&1
    git clean -fd >> "$LOG_FILE" 2>&1
    git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1
    git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1

    # Reaplica permissão do próprio script (caso o reset remova)
    chmod +x "$PROJECT_DIR/update.sh"

    log "✅ Código atualizado. Recriando containers..."

    # Derruba e sobe containers (Django vai usar RDS via .env)
    $DC down >> "$LOG_FILE" 2>&1
    $DC up --build -d >> "$LOG_FILE" 2>&1

    # Executa migrações automáticas do banco (agora apontando pro RDS)
    log "🔄 Aplicando migrações do banco no RDS..."
    $DC exec "$DJANGO_SERVICE" bash -c "python manage.py migrate --noinput" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "✅ Migrações aplicadas com sucesso."
        log "✅ Build concluído e servidor reiniciado com sucesso."
    else
        log "⚠️ ERRO ao aplicar migrações. Verifique o log acima."
    fi
else
    log "Nenhuma atualização detectada."
fi

log "==== Fim da execução ===="
