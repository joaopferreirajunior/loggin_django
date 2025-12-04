from django.core.management.base import BaseCommand
from users.services import S3ImageService


class Command(BaseCommand):
    help = 'Testa a configuração do S3 e IAM Role'

    def handle(self, *args, **options):
        self.stdout.write("Testando configuração AWS S3...")
        
        try:
            s3_service = S3ImageService()
            success, message = s3_service.test_s3_connection()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"{message}")
                )
                self.stdout.write(
                    f"Bucket: {s3_service.bucket_name}"
                )
                self.stdout.write(
                    f"Região: {s3_service.s3_client.meta.region_name}"
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"{message}")
                )
                self.stdout.write("\nChecklist para resolver:")
                self.stdout.write("1. Verifique se a instância EC2 tem uma IAM Role anexada")
                self.stdout.write("2. Verifique se a IAM Role tem permissões S3 adequadas")
                self.stdout.write("3. Verifique se o bucket S3 existe e está acessível")
                self.stdout.write("4. Verifique as variáveis de ambiente no .env")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erro inesperado: {str(e)}")
            )