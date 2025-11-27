# loggin_django
backend loggin django version

Virtual env
source loggin_venv/bin/activate

## Configuração de Ambiente

Configure a URL do frontend no arquivo `.env`:

**Desenvolvimento (padrão):**
```bash
FRONTEND_URL=http://localhost:8000
```

**Produção:**
```bash
FRONTEND_URL=http://3.236.36.55:8000
```

Esta variável é usada para:
- Links de recuperação de senha em emails
- Redirecionamentos de validação de token
- Configurações de CORS

**Script para alternar ambiente:**
```bash
# Desenvolvimento
./switch_env.sh dev

# Produção  
./switch_env.sh prod
```

Build do container:
docker compose up --build -d

Se precisar apenas atualizar o container com mudanças em views ou templates (sem migrations, mudanças em requiriments.txt, docker-compose...)
docker-compose restart django

Se precisar derrubar o container antigo para subir o novo
docker compose down && docker compose up --build -d

Se precisar forçar um rebuild completo (alterações no requirements.txt por exemplo)
docker compose build --no-cache && docker compose up -d


Se precisar destruir o container manualmente
docker kill loggin_django
docker rm loggin_django
docker kill loggin_postgres
docker rm loggin_postgres

logs de erros do build
docker compose logs --tail=50

logs de erros do container
docker logs loggin_django
docker logs loggin_postgres


Teste api (exemplo: criação de usuário):
# Substitua localhost por 3.236.36.55 para produção
curl -X POST http://localhost:8000/api/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'

curl -X POST http://3.236.36.55:8000/api/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "weber@blepol.com", "password": "medical25"}'

# Login com token JWT (retorna access + refresh tokens)
curl -X POST http://localhost:8000/api/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Requisição autenticada com token
curl -X GET http://localhost:8000/api/v0/me/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"

# Recuperação de senha
curl -X POST http://localhost:8000/api/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'

# Resposta (com links para teste em desenvolvimento):
# {
#   "detail": "Se o email usuario@email.com estiver registrado, você receberá instruções para recuperação de senha.",
#   "test_link": "http://localhost:8000/api/v0/validatetoken/?token=abc123token",
#   "test_token": "abc123token"
# }

# Validar token de recuperação (GET com query parameter)
curl -X GET "http://localhost:8000/api/v0/validatetoken/?token=abc123token"

# Reset de senha com token
curl -X POST http://localhost:8000/api/v0/resetpassword/ \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123token", "password": "novaSenha123"}'

## Fluxo de Recuperação de Senha:
1. Usuário solicita recuperação em: /recovery-password/
2. Sistema envia email com link: /api/v0/validatetoken/?token=abc123
3. Usuário clica no link do email
4. Backend valida token automaticamente:
   - Se válido: redireciona para /reset-password/?token=abc123
   - Se inválido: redireciona para /recovery-password/?error=token_invalid
5. Usuário define nova senha na página de reset
6. Token é invalidado após uso bem-sucedido

## API
Atualizar openapi-schema.yaml - python manage.py spectacular --format openapi --file openapi-schema.yaml
Visualizar com extensão Swagger Viewer - Clica com o direito em cima de openapi-schema.yaml e seleciona Preview Swagger


DEPLOY:
O deploy é feito sempre com o código disponível no repositório github. Se alterou, suba para o github.
Verifique o branch que será consultado pelo script em update.sh na maquina aws (EX: BRANCH="dev").

Antes de executar o deploy, faça todas as migrations!
Ative o ambiente virtual dentro do wsl: 
source loggin_venv/bin/activate

Garanta que o ambiente virtual esteja atualizado:
pip install -r requirements.txt
(Isso só precisa ser feito uma vez no ambiente virtual)

Faça todas as migrations:
python manage.py makemigrations

Para fazer o deploy através da maquina local rode ./deploy_aws.sh. Isso rodará o script ./update.sh dentro da maquina aws.
ou
Rode diretamente na maquina aws:
Entre na maquina aws EC2 via ssh: ssh -i ~/.ssh/loggin-key.pem ubuntu@ec2-3-236-36-55.compute-1.amazonaws.com
(editar o caminho para loggin-key.pem dentro do wsl. O caminho de loggin-key.pem no windows não é o mesmo que no wsl. É necessário copiar a chave para dentro da maquina virtual wsl)
dentro da maquina aws rode: ./update.sh
