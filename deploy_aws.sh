#!/bin/bash
# deploy_aws.sh - Dispara deploy na EC2 (loggin_django)

EC2_USER="ubuntu"
EC2_HOST="3.236.36.55"
SSH_KEY="$HOME/.ssh/loggin-key.pem" 
REMOTE_PROJECT_DIR="/home/ubuntu/loggin_django"
REMOTE_SCRIPT="update_aws.sh"

echo "Conectando em $EC2_USER@$EC2_HOST e executando $REMOTE_SCRIPT..."

ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "cd $REMOTE_PROJECT_DIR && ./update_aws.sh"
echo "Deploy concluído."
