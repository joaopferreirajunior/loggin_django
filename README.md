# loggin_django
backend loggin django version

Virtual env
source loggin_venv/bin/activate

Build do container:
docker compose up --build -d

Se precisar apenas atualizar o container com mudanças em views ou templates (sem migrations, mudanças em requiriments.txt, docker-compose...)
docker-compose restart django

Se precisar derrubar o container antigo para subir o novo
docker compose down && docker compose up --build -d

Se precisar forçar um rebuild completo (alterações no requirements.txt por exemplo)
docker compose build --no-cache
docker compose up -d

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
curl -X POST http://localhost:8000/api/v0/app/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'

API
Register:
username, password(original, sera criptografado no backend), email.
