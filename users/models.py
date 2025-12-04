from django.conf import settings
from django.db import models
from app.utils import AuditModel

#class Profile(models.Model):
#    user = models.OneToOneField(
#        settings.AUTH_USER_MODEL,
#        on_delete=models.CASCADE,
#        related_name="profile",
#    )
#    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
#    birth = models.DateField(null=True, blank=True)
#    phone = models.CharField(max_length=20, null=True, blank=True)
#
#    def __str__(self):
#        return f"Perfil de {self.user.get_username()}"

class Profile(AuditModel):
    # relação com o Django auth_user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    # Campos adicionaisv vindos do clickhouse
    
    cpf   = models.CharField(max_length=14, unique=True, null=True, blank=True)
    birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email_confirmed        = models.BooleanField(default=False)
    email_confirmed_at     = models.DateTimeField(null=True, blank=True)
    invited_at             = models.DateTimeField(null=True, blank=True)
    confirmation_token     = models.TextField(null=True, blank=True)
    confirmation_sent_at   = models.DateTimeField(null=True, blank=True)
    recovery_token         = models.TextField(null=True, blank=True)
    recovery_token_sent_at = models.DateTimeField(null=True, blank=True)
    clickhouse_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="UUID do usuário no ClickHouse")
    
    # Imagem de perfil - armazena apenas o path/key do S3
    profile_image = models.CharField(
        max_length=500, 
        null=True, 
        blank=True,
        help_text="Path da imagem de perfil no bucket S3 (ex: profiles/user_123/avatar.jpg)"
    )
    
    scratchpad = models.JSONField(default=dict, blank=True)


    def __str__(self):
        return f"Perfil de {self.user.get_username()}"
    
    def get_profile_image_url(self):
        """Retorna URL assinada temporária da imagem de perfil do S3"""
        if self.profile_image:
            try:
                from users.services import S3ImageService
                s3_service = S3ImageService()
                presigned_url = s3_service.generate_presigned_url(self.profile_image)
                return presigned_url
            except Exception as e:
                print(f"Erro ao gerar presigned URL: {e}")
                return None
        return None
    
    def delete_profile_image(self):
        """Remove a imagem do S3 e limpa o campo no banco"""
        if self.profile_image:
            try:
                import boto3
                from django.conf import settings
                
                # Usa IAM Role da instância EC2 automaticamente
                s3_client = boto3.client(
                    's3',
                    region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                )
                
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'loggin-media')
                s3_client.delete_object(Bucket=bucket_name, Key=self.profile_image)
                
                self.profile_image = None
                self.save()
                return True
            except Exception as e:
                print(f"Erro ao deletar imagem do S3: {e}")
                return False
        return True
    
    def get_user_role(self):
        """Retorna o papel/grupo principal do usuário"""
        user_groups = self.user.groups.values_list('name', flat=True)
        
        # Prioridade: system_admin > office_admin > regular_user
        if 'system_admin' in user_groups:
            return 'system_admin'
        elif 'office_admin' in user_groups:
            return 'office_admin'
        elif 'regular_user' in user_groups:
            return 'regular_user'
        else:
            return 'no_role'
    
    def is_system_admin(self):
        """Verifica se o usuário é administrador do sistema"""
        return self.user.groups.filter(name='system_admin').exists()
    
    def is_office_admin(self):
        """Verifica se o usuário é administrador de escritório"""
        return self.user.groups.filter(name='office_admin').exists()
    
    def is_regular_user(self):
        """Verifica se o usuário é usuário regular"""
        return self.user.groups.filter(name='regular_user').exists()
    
    def can_manage_users(self):
        """Verifica se o usuário pode gerenciar outros usuários"""
        return (self.user.has_perm('users.can_manage_system') or 
                self.user.has_perm('users.can_manage_office_users'))
    
    def can_view_all_users(self):
        """Verifica se o usuário pode ver todos os usuários"""
        return self.user.has_perm('users.can_view_all_users')
    
    def can_access_admin(self):
        """Verifica se o usuário pode acessar o painel admin"""
        return self.user.has_perm('users.can_access_admin_panel')
    
    @classmethod
    def assign_role(cls, user, role):
        """Atribui um papel específico ao usuário"""
        from django.contrib.auth.models import Group
        
        # Remove todos os grupos de papel existentes
        user.groups.filter(name__in=['system_admin', 'office_admin', 'regular_user']).delete()
        
        # Adiciona o novo papel
        if role in ['system_admin', 'office_admin', 'regular_user']:
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            return True
        return False
    
