from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings


class Command(BaseCommand):
    help = 'Verifica se todas as configurações estão corretas'

    def handle(self, *args, **options):
        self.stdout.write("Verificando configuração do sistema...")
        
        # Verificar apps instalados
        self.stdout.write("\n1. Apps instalados:")
        for app in settings.INSTALLED_APPS:
            if app.startswith(('loggin', 'users', 'devices', 'projects')):
                self.stdout.write(f"   - {app}")
        
        # Verificar URLs principais
        self.stdout.write("\n2. Testando URLs principais:")
        try:
            urls_to_test = [
                'api_web_login',
                'api_mobile_login', 
                'api_web_me',
                'api_mobile_me',
                'upload_profile_image'
            ]
            
            for url_name in urls_to_test:
                try:
                    url = reverse(url_name)
                    self.stdout.write(f"   ✓ {url_name}: {url}")
                except:
                    self.stdout.write(f"   ✗ {url_name}: ERRO")
                    
        except Exception as e:
            self.stdout.write(f"   Erro ao testar URLs: {e}")
        
        # Verificar configurações S3
        self.stdout.write("\n3. Configurações S3:")
        s3_settings = [
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_S3_REGION_NAME'
        ]
        
        for setting in s3_settings:
            value = getattr(settings, setting, 'NÃO DEFINIDO')
            self.stdout.write(f"   - {setting}: {value}")
        
        # Verificar se migrations estão aplicadas
        self.stdout.write("\n4. Verificando modelos:")
        try:
            from users.models import Profile
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            self.stdout.write("   ✓ Modelo User carregado")
            self.stdout.write("   ✓ Modelo Profile carregado")
            
            # Verificar campo profile_image
            profile_fields = [f.name for f in Profile._meta.fields]
            if 'profile_image' in profile_fields:
                self.stdout.write("   ✓ Campo profile_image existe")
            else:
                self.stdout.write("   ✗ Campo profile_image NÃO EXISTE")
                
        except Exception as e:
            self.stdout.write(f"   Erro ao verificar modelos: {e}")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("Verificação concluída!")