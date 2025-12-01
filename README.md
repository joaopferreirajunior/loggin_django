# Medical San Logging Django

Sistema backend loggin desenvolvido em Django.

## 🚀 Início Rápido

### Ambiente Virtual
```bash
source loggin_venv/bin/activate
(Simula o ambiente da EC2 para testes locais)
```

### Configuração de Ambiente EC2

Configure as variáveis de ambiente no arquivo `.env`:

**Desenvolvimento (padrão):**
```bash
FRONTEND_URL=http://localhost:8000
```

**Produção:**
```bash
FRONTEND_URL=http://3.236.36.55:8000 
(Trocar IP para o domínio quando tiver um)
```

**Scripts de alternância de ambiente:**
```bash
# Desenvolvimento
./switch_env.sh dev

# Produção  
./switch_env.sh prod
```
Rodar na EC2 ou no ambiente local antes do build

## 🐳 Docker

### Comandos Básicos

**Build inicial do container:**
```bash
docker compose up --build -d
```

**Restart simples (mudanças em views/templates):**
```bash
docker-compose restart django
```

**Rebuild com alterações:**
```bash
docker compose down && docker compose up --build -d
```

**Rebuild completo (alterações no requirements.txt):**
```bash
docker compose build --no-cache && docker compose up -d
```

### Gerenciamento de Containers

**Destruir containers manualmente:**
```bash
docker kill loggin_django
docker rm loggin_django

docker kill loggin_postgres
docker rm loggin_postgres
```

**Visualizar logs:**
```bash
# Logs do build
docker compose logs --tail=50

# Logs dos containers
docker logs loggin_django
docker logs loggin_postgres
```

## 🔗 API Endpoints

### Autenticação

**Registro de usuário:**
```bash
# Desenvolvimento
curl -X POST http://localhost:8000/api/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'
```

**Login (JWT):**
```bash
# Desenvolvimento
curl -X POST http://localhost:8000/api/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Produção
curl -X POST http://3.236.36.55:8000/api/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "weber@blepol.com", "password": "medical25"}'
```

**Requisição autenticada:**
```bash
curl -X GET http://localhost:8000/api/v0/me/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

### Recuperação de Senha

**Solicitar recuperação:**
```bash
curl -X POST http://localhost:8000/api/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'
```

**Resposta (desenvolvimento com tokens de teste):**
```json
{
  "detail": "Se o email usuario@email.com estiver registrado, você receberá instruções para recuperação de senha.",
  "test_link": "http://localhost:8000/api/v0/validatetoken/?token=abc123token",
  "test_token": "abc123token"
}
```

**Validar token:**
```bash
curl -X GET "http://localhost:8000/api/v0/validatetoken/?token=abc123token"
```

**Reset de senha:**
```bash
curl -X POST http://localhost:8000/api/v0/resetpassword/ \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123token", "password": "novaSenha123"}'
```

### 🔄 Fluxo de Recuperação de Senha

1. **Solicitação**: Usuário acessa `/recovery-password/` e informa email
2. **Email**: Sistema envia link: `/api/v0/validatetoken/?token=abc123`
3. **Validação**: Usuário clica no link do email
4. **Redirecionamento automático**:
   - Token válido → `/reset-password/?token=abc123`
   - Token inválido → `/recovery-password/?error=token_invalid`
5. **Nova senha**: Usuário define nova senha na página de reset
6. **Finalização**: Token é invalidado após uso bem-sucedido

## 📚 Documentação da API

**Gerar schema OpenAPI:**
```bash
python manage.py spectacular --format openapi --file openapi-schema.yaml
```

**Visualizar documentação:**
- Clique com botão direito em `openapi-schema.yaml`
- Selecione "Preview Swagger"

**URLs da documentação (após configuração):**
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- Schema JSON: `/api/schema/`

## 🚀 Deploy AWS EC2

### ⚠️ Pré-requisitos

1. **Código no GitHub**: Sempre faça push das alterações antes do deploy
2. **Branch**: Verifique o branch configurado em `update.sh` (ex: `BRANCH="dev"`)

### Preparação local antes do deploy

**1. Ativar ambiente virtual (WSL):**
```bash
source loggin_venv/bin/activate
```

**2. Atualizar dependências:**
```bash
pip install -r requirements.txt
```

**3. Fazer migrações:**
```bash
python manage.py makemigrations
```

### Execução do Deploy

**Opção 1: Deploy a partir da máquina local (recomendado):**
```bash
./deploy_aws.sh
```

**Opção 2: Puxar deploy direto na AWS:**
```bash
# Conectar via SSH
ssh -i ~/.ssh/loggin-key.pem ubuntu@ec2-3-236-36-55.compute-1.amazonaws.com

# Executar update
./update.sh
```

> **Nota**: Para WSL, copie a chave SSH para dentro da máquina virtual, pois os caminhos Windows não são compatíveis.

## 🔧 Estrutura do Projeto

```
loggin_django/
├── app/                 # Configurações principais
├── web/                 # Interface web e APIs
├── users/               # Gerenciamento de usuários, paciêntes e outras entidades humanas
├── mobile/              # APIs para mobile
├── devices/             # APIs para dados de equipamentos
├── projects/            # APIs para projetos
├── docker-compose.yml   # Configuração Docker
├── requirements.txt     # Dependências Python
└── update.sh           # Script de deploy automático
```
