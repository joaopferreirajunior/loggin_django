# Medical San Loggin Django

Sistema backend loggin desenvolvido em Django.

## Início Rápido

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

## Docker

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

## API Endpoints

### Autenticação

**Registro de usuário:**
```bash
# Desenvolvimento - Web
curl -X POST http://localhost:8000/users/api/web/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'

# Desenvolvimento - Mobile
curl -X POST http://localhost:8000/users/api/mobile/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'
```

**Login (JWT):**
```bash
# Desenvolvimento - Web
curl -X POST http://localhost:8000/users/api/web/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Desenvolvimento - Mobile  
curl -X POST http://localhost:8000/users/api/mobile/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Produção - Web
curl -X POST http://3.236.36.55:8000/users/api/web/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "weber@blepol.com", "password": "medical25"}'
```

**Requisição autenticada:**
```bash
curl -X GET http://localhost:8000/users/api/web/v0/me/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

### Gerenciamento de Perfil

**Obter dados do usuário (com imagem):**
```bash
curl -X GET http://localhost:8000/users/api/web/v0/profile/image/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Upload de imagem de perfil:**
```bash
curl -X POST http://localhost:8000/users/api/web/v0/profile/image/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -F "profile_image=@/caminho/para/imagem.jpg"
```

**Remover imagem de perfil:**
```bash
curl -X DELETE http://localhost:8000/users/api/web/v0/profile/image/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Obter URL da imagem de perfil:**
```bash
# Desenvolvimento
curl -X GET http://localhost:8000/users/api/web/v0/profile/image/123/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Produção
curl -X GET http://3.236.36.55:8000/users/api/web/v0/profile/image/2/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Resposta:
# {
#   "profile_image_url": "https://medicalsan-uploads.s3.us-east-1.amazonaws.com/profiles/user_2/avatar.jpg?X-Amz-Algorithm=...",
#   "expires_in": 3600
# }
```

**Usar a URL para visualizar/baixar a imagem:**
```bash
# A URL retornada pode ser usada diretamente no navegador ou em requisições HTTP
# Exemplo: copie a URL do campo "profile_image_url" e acesse no navegador
# Ou use com curl para baixar:
curl -o imagem_perfil.jpg "URL_PRESIGNED_COMPLETA_AQUI"
```

### Notas sobre URLs de Imagem

1. **Endpoint `/profile/image/<user_id>/`**: Retorna JSON com URL presigned válida por 1 hora
2. **URL presigned**: Link direto para imagem no S3, válido temporariamente (3600 segundos)
3. **Endpoint `/profile/image/`** (sem user_id): Retorna dados do perfil incluindo URL presigned
4. **Segurança**: URLs presigned permitem acesso temporário sem necessidade de autenticação adicional

### Upload de imagem

1. **Token JWT**: Certifique-se de que o token está válido e não expirou (5 minutos de validade)
2. **Tamanho**: Backend aceita máximo 5MB, valide localmente primeiro
3. **Formatos**: JPG, PNG, WebP são suportados
4. **Redimensionamento**: Backend redimensiona automaticamente para 800x800px
5. **Segurança S3**: Bucket configurado como privado - imagens acessíveis via:
   - **URLs Presigned**: URLs temporárias com expiração de 1 hora (3600 segundos)
   - **Endpoint GET `/profile/image/<user_id>/`**: Retorna JSON com URL presigned válida
6. **Renovação de Token**: Se o token expirar, faça login novamente para obter novo access_token

### Recuperação de Senha

**Solicitar recuperação:**
```bash
# Web
curl -X POST http://localhost:8000/users/api/web/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'

# Mobile
curl -X POST http://localhost:8000/users/api/mobile/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'
```

**Resposta (desenvolvimento com tokens de teste):**
```json
{
  "detail": "Se o email usuario@email.com estiver registrado, você receberá instruções para recuperação de senha.",
  "test_link": "http://localhost:8000/users/api/web/v0/validatetoken/?token=abc123token",
  "test_token": "abc123token"
}
```

**Validar token:**
```bash
curl -X GET "http://localhost:8000/users/api/web/v0/validatetoken/?token=abc123token"
```

**Reset de senha:**
```bash
curl -X POST http://localhost:8000/users/api/web/v0/resetpassword/ \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123token", "password": "novaSenha123"}'
```

### Gerenciamento de Pacientes

**Listar pacientes:**
```bash
# Web
curl -X GET http://localhost:8000/patients/api/web/v0/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X GET http://localhost:8000/patients/api/mobile/v0/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Criar paciente:**
```bash
# Web
curl -X POST http://localhost:8000/patients/api/web/v0/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "fullName": "Maria da Silva",
    "birthDate": "1985-03-15",
    "gender": "FEMALE",
    "cpf": "123.456.789-00",
    "phone": "(11) 99999-9999",
    "email": "maria@email.com",
    "fullAddress": "Rua das Flores, 123",
    "city": "São Paulo",
    "region": "SP",
    "cep": "01234-567"
  }'

# Mobile
curl -X POST http://localhost:8000/patients/api/mobile/v0/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "fullName": "João Santos",
    "birthDate": "1990-07-22",
    "gender": "MALE",
    "cpf": "987.654.321-00",
    "phone": "(11) 88888-8888"
  }'
```

**Obter paciente específico:**
```bash
# Web
curl -X GET http://localhost:8000/patients/api/web/v0/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X GET http://localhost:8000/patients/api/mobile/v0/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Atualizar paciente:**
```bash
# Web - Atualização parcial (PATCH)
curl -X PATCH http://localhost:8000/patients/api/web/v0/550e8400-e29b-41d4-a716-446655440000/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{"phone": "(11) 77777-7777", "email": "novoemail@email.com"}'

# Mobile - Atualização completa (PUT)
curl -X PUT http://localhost:8000/patients/api/mobile/v0/550e8400-e29b-41d4-a716-446655440000/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "fullName": "João Santos Silva",
    "birthDate": "1990-07-22",
    "gender": "MALE",
    "cpf": "987.654.321-00",
    "phone": "(11) 77777-7777",
    "email": "joao.santos@email.com",
    "isActive": true
  }'
```

**Remover paciente (soft delete):**
```bash
# Web
curl -X DELETE http://localhost:8000/patients/api/web/v0/550e8400-e29b-41d4-a716-446655440000/delete/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X DELETE http://localhost:8000/patients/api/mobile/v0/550e8400-e29b-41d4-a716-446655440000/delete/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

### Gerenciamento de Prontuários

**Listar prontuários de um paciente:**
```bash
# Web
curl -X GET http://localhost:8000/patients/api/web/v0/550e8400-e29b-41d4-a716-446655440000/records/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X GET http://localhost:8000/patients/api/mobile/v0/550e8400-e29b-41d4-a716-446655440000/records/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Criar prontuário médico:**
```bash
# Web
curl -X POST http://localhost:8000/patients/api/web/v0/mrecords/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "patientId": "550e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2025-12-04T14:30:00Z",
    "doctorName": "Dr. Carlos Silva",
    "complaint": "Dor de cabeça persistente há 3 dias",
    "clinicalNotes": "Paciente apresenta cefaleia frontal, sem febre. Pressão arterial normal.",
    "anamnese": {
      "symptoms": ["dor de cabeça", "cansaço"],
      "duration": "3 dias",
      "intensity": 7,
      "medications": ["paracetamol"]
    }
  }'

# Mobile
curl -X POST http://localhost:8000/patients/api/mobile/v0/mrecords/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "patientId": "550e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2025-12-04T15:00:00Z",
    "doctorName": "Dr. Ana Costa",
    "complaint": "Consulta de rotina",
    "clinicalNotes": "Paciente em bom estado geral, sem queixas.",
    "anamnese": {
      "type": "routine_check",
      "blood_pressure": "120/80",
      "weight": "70kg",
      "height": "1.75m"
    }
  }'
```

**Atualizar prontuário médico:**
```bash
# Web
curl -X PATCH http://localhost:8000/patients/api/web/v0/mrecords/660e8400-e29b-41d4-a716-446655440000/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "clinicalNotes": "Paciente apresenta melhora significativa após medicação.",
    "anamnese": {
      "symptoms": ["dor de cabeça leve"],
      "duration": "1 dia",
      "intensity": 3,
      "medications": ["paracetamol", "ibuprofeno"],
      "follow_up": "Retorno em 1 semana se sintomas persistirem"
    }
  }'

# Mobile
curl -X PUT http://localhost:8000/patients/api/mobile/v0/mrecords/660e8400-e29b-41d4-a716-446655440000/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -d '{
    "patientId": "550e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2025-12-04T15:00:00Z",
    "doctorName": "Dr. Ana Costa",
    "complaint": "Consulta de rotina - Retorno",
    "clinicalNotes": "Paciente retorna para avaliação. Estado geral excelente.",
    "anamnese": {
      "type": "follow_up",
      "blood_pressure": "118/78",
      "weight": "69kg",
      "improvement": "significativa"
    }
  }'
```

### Gerenciamento de Fotos de Pacientes

**Upload de foto do paciente:**
```bash
# Web
curl -X POST http://localhost:8000/patients/api/web/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -F "photo=@/caminho/para/foto.jpg"

# Mobile
curl -X POST http://localhost:8000/patients/api/mobile/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -F "photo=@/caminho/para/foto.jpg"
```

**Obter URL da foto do paciente:**
```bash
# Web - Desenvolvimento
curl -X GET http://localhost:8000/patients/api/web/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Web - Produção
curl -X GET http://3.236.36.55:8000/patients/api/web/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X GET http://localhost:8000/patients/api/mobile/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Resposta:
# {
#   "photo_url": "https://loggin-media.s3.amazonaws.com/profiles/patient_550e8400.../photo.jpg?X-Amz-Algorithm=...",
#   "expires_in": 3600
# }
```

**Remover foto do paciente:**
```bash
# Web
curl -X DELETE http://localhost:8000/patients/api/web/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Mobile
curl -X DELETE http://localhost:8000/patients/api/mobile/v0/image/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Notas sobre fotos de pacientes:**
1. **URL presigned**: Retorna link temporário válido por 1 hora (3600 segundos)
2. **Formato**: Mesmo padrão das fotos de perfil de usuários
3. **Tamanho máximo**: 5MB
4. **Formatos suportados**: JPG, PNG, WebP
5. **Redimensionamento**: Automático para 800x800px

### Fluxo de Recuperação de Senha

1. **Solicitação**: Usuário acessa `/recovery-password/` e informa email
2. **Email**: Sistema envia link: `/users/api/web/v0/validatetoken/?token=abc123`
3. **Validação**: Usuário clica no link do email
4. **Redirecionamento automático**:
   - Token válido → `/reset-password/?token=abc123`
   - Token inválido → `/recovery-password/?error=token_invalid`
5. **Nova senha**: Usuário define nova senha na página de reset
6. **Finalização**: Token é invalidado após uso bem-sucedido

## Documentação da API

**Gerar schema OpenAPI:**
```bash
python manage.py spectacular --format openapi --file openapi-schema.yaml
```

**Visualizar documentação:**
- Clique com botão direito em `openapi-schema.yaml`
- Selecione "Preview Swagger"

**URLs da documentação (após configuração):**
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`  
- Schema JSON: `http://localhost:8000/api/schema/`

### Organização da Documentação

A API está organizada em seções distintas:

**Web APIs**:
- **Web - Auth**: Login, registro, recuperação de senha para aplicação web (`/users/api/web/v0/`)
- **Web - User**: Gerenciamento de usuários e perfis para aplicação web (`/users/api/web/v0/`)
- **Web - Patients**: Gerenciamento de pacientes e prontuários para aplicação web (`/patients/api/web/v0/`)

**Mobile APIs**:
- **Mobile - Auth**: Login, registro, recuperação de senha para aplicação mobile (`/users/api/mobile/v0/`)
- **Mobile - User**: Gerenciamento de usuários e perfis para aplicação mobile (`/users/api/mobile/v0/`)
- **Mobile - Patients**: Gerenciamento de pacientes e prontuários para aplicação mobile (`/patients/api/mobile/v0/`)

## Deploy AWS EC2

### Pré-requisitos

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

### Comandos de Manutenção

**Limpar perfis órfãos (profiles sem usuário):**
```bash
python manage.py cleanup_orphan_profiles
```

**Configurar grupos de usuários e permissões:**
```bash
python manage.py setup_user_groups
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

## Estrutura do Projeto

```
loggin_django/
├── app/                 # Configurações principais  
├── loggin/              # App principal consolidado
│   ├── api/             # APIs organizadas por cliente
│   │   ├── web/v0/      # Endpoints para aplicação web
│   │   └── mobile/v0/   # Endpoints para aplicação mobile
│   └── templates/       # Templates HTML
├── users/               # Gerenciamento de usuários e perfis
│   ├── services.py      # Serviço S3 para upload de imagens
│   └── api/v0/          # APIs de usuários (upload de imagem)
├── patients/            # Gerenciamento de pacientes e prontuários
│   └── api/             # APIs separadas por plataforma
│       ├── web/v0/      # Endpoints para aplicação web
│       └── mobile/v0/   # Endpoints para aplicação mobile
├── devices/             # APIs para dados de equipamentos
├── projects/            # APIs para projetos
├── docker-compose.yml   # Configuração Docker
├── requirements.txt     # Dependências Python
└── update.sh           # Script de deploy automático
```

wsl
source loggin_venv/bin/activate
curl -X POST http://3.236.36.55:8000/users/api/web/v0/login/   -H "Content-Type: application/json"   -d '{"username": "juanherrera", "password": "ju33257194ju"}'




# Web - Produção
curl -X GET http://3.236.36.55:8000/patients/api/web/v0/image/3e9a04e5-a149-4ef4-be38-a120155f9907/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1ODkxMjkwLCJpYXQiOjE3NjU4OTA5OTAsImp0aSI6Ijc2NGI5Y2ZiNzM3MTRjZmI4ZmQ3OTY3OTI5MjM4ODA3IiwidXNlcl9pZCI6IjIifQ.KhuQY2Vg-OEIB1fBFW0CydSoq1WHDnb3K27civ3Lh58"

# Mobile
curl -X GET http://3.236.36.55:8000/patients/api/mobile/v0/image/3e9a04e5-a149-4ef4-be38-a120155f9907/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1ODkxMjkwLCJpYXQiOjE3NjU4OTA5OTAsImp0aSI6Ijc2NGI5Y2ZiNzM3MTRjZmI4ZmQ3OTY3OTI5MjM4ODA3IiwidXNlcl9pZCI6IjIifQ.KhuQY2Vg-OEIB1fBFW0CydSoq1WHDnb3K27civ3Lh58"


# Teste - Remover

# Login
curl -X POST http://3.236.36.55:8000/users/api/mobile/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joaopferreirajunior", "password": "ju33257194ju"}'

# Device 1
curl -X POST http://3.236.36.55:8000/devices/api/mobile/v0/devices/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{"serial": "TESTE-WEBER-USA", "model": "Hakon - USA"}'

# Device 2
curl -X POST http://3.236.36.55:8000/devices/api/mobile/v0/devices/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{"serial": "TEST-WEBER", "model": "Ultramed MPT"}'