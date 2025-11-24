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

# Se houver atualização, sincroniza com o remoto
if [ "$OLD_HASH" != "$NEW_HASH" ]; then
    log "🚀 Atualização remota detectada — sincronizando código..."

    git reset --hard HEAD >> "$LOG_FILE" 2>&1
    git clean -fd >> "$LOG_FILE" 2>&1
    git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1
    git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1

    chmod +x "$PROJECT_DIR/update.sh"

    log "✅ Código sincronizado com o remoto."
else
    log "Nenhuma atualização remota. Usando código local atual (inclui modificações locais)."
fi

# Configura FRONTEND_URL com IP público da própria EC2 (depois do git reset!)
log "Configurando FRONTEND_URL com IP público da instância..."
if [ -f ".env" ]; then
    # Tenta IMDSv2
    TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
      -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

    if [ -n "$TOKEN" ]; then
        PUBLIC_IP=$(curl -s "http://169.254.169.254/latest/meta-data/public-ipv4" \
          -H "X-aws-ec2-metadata-token: $TOKEN")
    else
        # Fallback IMDSv1
        PUBLIC_IP=$(curl -s "http://169.254.169.254/latest/meta-data/public-ipv4")
    fi

    log "PUBLIC_IP detectado: ${PUBLIC_IP:-<vazio>}"

    if [ -n "$PUBLIC_IP" ]; then
        if grep -q '^FRONTEND_URL=' .env; then
            sed -i "s|^FRONTEND_URL=.*|FRONTEND_URL=http://$PUBLIC_IP:8000|g" .env
            log "✅ FRONTEND_URL atualizado para http://$PUBLIC_IP:8000"
        else
            echo "FRONTEND_URL=http://$PUBLIC_IP:8000" >> .env
            log "✅ FRONTEND_URL adicionado como http://$PUBLIC_IP:8000"
        fi
    else
        log "⚠️ Não foi possível obter o IP público da instância. FRONTEND_URL não foi alterado."
    fi
else
    log "⚠️ Arquivo .env não encontrado"
fi

log "✅ Recriando containers..."
$DC down >> "$LOG_FILE" 2>&1
$DC up --build -d >> "$LOG_FILE" 2>&1

log "🔄 Aplicando migrações do banco no RDS..."
$DC exec "$DJANGO_SERVICE" bash -c "python manage.py migrate --noinput" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "✅ Migrações aplicadas com sucesso."
    log "✅ Build concluído e servidor reiniciado com sucesso."
else
    log "⚠️ ERRO ao aplicar migrações. Verifique o log acima."
fi

log "==== Fim da execução ===="
