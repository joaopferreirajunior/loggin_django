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
