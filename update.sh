#!/bin/bash
# ============================
# update.sh - Auto Deploy Django + Docker (branch dev)
# ============================

PROJECT_DIR="/home/ubuntu/loggin_django"
LOG_FILE="$PROJECT_DIR/update_aws.log"
BRANCH="dev"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR" || {
    log "ERRO: diretório $PROJECT_DIR não encontrado."
    exit 1
}

# Verifica dependências básicas
if ! command -v git &> /dev/null; then log "ERRO: git não encontrado."; exit 1; fi
if ! command -v docker &> /dev/null; then log "ERRO: docker não encontrado."; exit 1; fi

log "==== Iniciando verificação de atualização ===="

# Busca atualizações do repositório remoto
if ! git fetch origin "$BRANCH" > /dev/null 2>&1; then
    log "ERRO: falha ao buscar atualizações do repositório."
    exit 1
fi

OLD_HASH=$(git rev-parse HEAD)
NEW_HASH=$(git rev-parse "origin/$BRANCH")

log "Hash atual: $OLD_HASH"
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

    log "✅ Código atualizado. Limpando cache Docker..."
    docker builder prune -af > /dev/null 2>&1

    log "🔧 Recriando containers..."
    docker compose down >> "$LOG_FILE" 2>&1
    docker compose up --build -d >> "$LOG_FILE" 2>&1

    # Executa migrações automáticas do banco de dados
    log "🔄 Aplicando migrações do banco..."
    docker exec -i loggin_django bash -c "python manage.py migrate --noinput" >> "$LOG_FILE" 2>&1

    log "✅ Migrações aplicadas com sucesso."
    log "✅ Build concluído e servidor reiniciado com sucesso."
else
    log "Nenhuma atualização detectada."
fi

log "==== Fim da execução ===="
