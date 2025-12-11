from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from users.models import Profile
from users.services import S3ImageService

# DRF Spectacular imports
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

User = get_user_model()

class DetailSerializer(serializers.Serializer):
    """Usado para mensagens simples: {"detail": "..."}"""
    detail = serializers.CharField()

class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    # Campo username customizado para remover validação padrão do Django em inglês
    username = serializers.CharField(
        required=True,
        max_length=150,
        help_text="Nome de usuário (apenas letras e números)"
    )
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150, help_text="Nome do usuário")
    last_name = serializers.CharField(required=True, max_length=150, help_text="Sobrenome do usuário")
    # campos adicionais para o perfil
    cpf = serializers.CharField(required=True, help_text="CPF do usuário")
    birth = serializers.DateField(required=False, allow_null=True, help_text="Data de nascimento")
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Telefone")

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'cpf', 'birth', 'phone')

    def validate_email(self, value):
        """Validação customizada para email único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value

    def validate_username(self, value):
        """Validação customizada para username único"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "O nome de usuário só pode conter letras e números."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value
    
    def validate_cpf(self, value):
        """Validação customizada para CPF único"""
        if Profile.objects.filter(cpf=value).exists():
            raise serializers.ValidationError("Este CPF já está em uso.")
        return value

    def create(self, validated_data):
        """Criação de usuário com senha criptografada"""
        # Extrai campos do perfil
        cpf = validated_data.pop('cpf')
        birth = validated_data.pop('birth', None)
        phone = validated_data.pop('phone', None)
        
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Criar profile automaticamente com dados do perfil
        Profile.objects.create(
            user=user,
            cpf=cpf,
            birth=birth,
            phone=phone
        )
        
        return user

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer do perfil do usuário"""
    profile_image_url = serializers.SerializerMethodField()
    # Campos do User para permitir edição junto com o profile
    email = serializers.EmailField(source='user.email', help_text="Email do usuário")
    first_name = serializers.CharField(source='user.first_name', help_text="Nome do usuário", max_length=150, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', help_text="Sobrenome do usuário", max_length=150, allow_blank=True)
    
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'cpf', 'birth', 'phone', 'email',
                 'email_confirmed', 'email_confirmed_at', 'invited_at', 
                 'confirmation_sent_at', 'clickhouse_id',
                 'profile_image_url')
        read_only_fields = (
            'email_confirmed', 'email_confirmed_at', 'invited_at',
            'confirmation_sent_at', 'clickhouse_id',
            'profile_image_url'
        )
    
    def get_profile_image_url(self, obj) -> str:
        """Retorna a URL da imagem de perfil"""
        return obj.get_profile_image_url()
    
    def update(self, instance, validated_data):
        """Atualiza tanto o Profile quanto os campos do User"""
        # Extrai dados do User se existirem
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Verifica se o email está sendo alterado
        email_changed = False
        if 'email' in user_data:
            current_email = instance.user.email
            new_email = user_data['email']
            if current_email != new_email:
                email_changed = True
        
        # Atualiza o Profile
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Se o email foi alterado, reseta a confirmação
        if email_changed:
            instance.email_confirmed = False
            instance.email_confirmed_at = None
        
        instance.save()
        
        # Atualiza o User se houver dados
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        return instance

class UserSerializer(serializers.ModelSerializer):
    """Serializer completo do usuário com perfil"""
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'profile', 'permissions')
    
    def get_full_name(self, obj):
        """Retorna nome completo baseado nos campos first_name e last_name do User"""
        return obj.get_full_name() or obj.username
    
    def get_permissions(self, obj):
        """Retorna permissões completas do usuário"""
        profile = obj.profile
        return {
            'user_role': profile.get_user_role(),
            'is_system_admin': profile.is_system_admin(),
            'is_office_admin': profile.is_office_admin(),
            'is_regular_user': profile.is_regular_user(),
            'roles': [group.name for group in obj.groups.all()],
            'permissions': list(obj.get_all_permissions()),
            'can_manage_users': profile.can_manage_users(),
            'can_view_all_users': profile.can_view_all_users(),
            'can_access_admin': profile.can_access_admin(),
        }

class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField(
        help_text="Username ou email do usuário"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Senha do usuário"
    )

class LoginResponseSerializer(serializers.Serializer):
    """Serializer para resposta de login"""
    detail = serializers.CharField()
    user = UserSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()

class AuthResponseSerializer(serializers.Serializer):
    """Serializer para respostas de autenticação"""
    detail = serializers.CharField()

class PasswordRecoverySerializer(serializers.Serializer):
    """Serializer para recuperação de senha"""
    email = serializers.EmailField(help_text="Email para recuperação")

class PasswordRecoveryResponseSerializer(serializers.Serializer):
    """Serializer para resposta de recuperação"""
    detail = serializers.CharField()
    test_token = serializers.CharField(required=False)

class PasswordResetSerializer(serializers.Serializer):
    """Serializer para reset de senha"""
    token = serializers.CharField(help_text="Token de recuperação")
    password = serializers.CharField(
        min_length=8,
        help_text="Nova senha (mínimo 8 caracteres)"
    )

class TokenValidationSerializer(serializers.Serializer):
    """Serializer para validação de token"""
    valid = serializers.BooleanField()

class UserPermissionsSerializer(serializers.Serializer):
    """Serializer para permissões do usuário"""
    user_role = serializers.CharField()
    is_system_admin = serializers.BooleanField()
    is_office_admin = serializers.BooleanField()
    is_regular_user = serializers.BooleanField()
    roles = serializers.ListField(child=serializers.CharField())
    permissions = serializers.ListField(child=serializers.CharField())
    can_manage_users = serializers.BooleanField()
    can_view_all_users = serializers.BooleanField()
    can_access_admin = serializers.BooleanField()
    
    def to_representation(self, instance):
        """Converte o usuário em dados de permissões"""
        profile = instance.profile
        
        return {
            'user_role': profile.get_user_role(),
            'is_system_admin': profile.is_system_admin(),
            'is_office_admin': profile.is_office_admin(),
            'is_regular_user': profile.is_regular_user(),
            'roles': [group.name for group in instance.groups.all()],
            'permissions': list(instance.get_all_permissions()),
            'can_manage_users': profile.can_manage_users(),
            'can_view_all_users': profile.can_view_all_users(),
            'can_access_admin': profile.can_access_admin(),
        }

class RoleAssignmentSerializer(serializers.Serializer):
    """Serializer para atribuição de roles"""
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['system_admin', 'office_admin', 'regular_user'])
    
    def save(self, current_user):
        """Atribui o role ao usuário"""
        user_id = self.validated_data['user_id']
        role = self.validated_data['role']
        
        # Verifica se o usuário atual pode alterar roles
        if not (current_user.groups.filter(name='system_admin').exists() or 
               current_user.has_perm('auth.change_user')):
            raise PermissionError("Você não tem permissão para alterar roles de usuário")
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("Usuário não encontrado")
        
        # Remove roles anteriores
        target_user.groups.clear()
        
        # Adiciona novo role se não for regular_user
        if role != 'regular_user':
            group, _ = Group.objects.get_or_create(name=role)
            target_user.groups.add(group)
        
        return f"Role '{role}' atribuído ao usuário '{target_user.username}' com sucesso"

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Upload de imagem de perfil",
            description="Arquivo de imagem para upload (JPEG, PNG, WebP até 5MB)",
            value={
                "profile_image": "binary_image_data"
            },
        )
    ]
)
class ProfileImageUploadSerializer(serializers.Serializer):
    """
    Serializer para upload de imagem de perfil
    """
    profile_image = serializers.ImageField(
        required=True,
        help_text="Imagem de perfil (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_profile_image(self, value):
        """
        Valida a imagem usando o serviço S3ImageService
        """
        s3_service = S3ImageService()
        is_valid, error_message = s3_service.validate_image(value)
        
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value
    
    def save(self, user):
        """
        Processa e salva a imagem no S3
        """
        try:
            profile_image = self.validated_data['profile_image']
            s3_service = S3ImageService()
            
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Remove imagem anterior se existir
            if profile.profile_image:
                profile.delete_profile_image()
            
            # Upload nova imagem
            success, message, s3_key = s3_service.process_and_upload_profile_image(
                user.id, profile_image
            )
            
            if not success:
                raise serializers.ValidationError(f"Erro no upload: {message}")
            
            # Atualiza o profile com o novo path
            profile.profile_image = s3_key
            profile.save()
            
            return profile
            
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log the full error for debugging
            import traceback
            print(f"Erro completo no upload: {traceback.format_exc()}")
            raise serializers.ValidationError(f"Erro interno no upload: {str(e)}")

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Profile com imagem",
            value={
                "id": 1,
                "username": "joao123",
                "email": "joao@email.com",
                "profile": {
                    "cpf": "12345678901",
                    "birth": "1990-01-15", 
                    "phone": "(11) 99999-9999",
                    "profile_image_url": "https://medicalsan-uploads.s3.us-east-1.amazonaws.com/profiles/user_1/avatar_123.jpg"
                }
            }
        )
    ]
)
class UserWithImageSerializer(serializers.ModelSerializer):
    """
    Serializer do usuário incluindo URL da imagem de perfil
    """
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
    
    def get_profile(self, obj) -> dict:
        """Retorna dados do perfil incluindo URL da imagem"""
        try:
            profile = obj.profile
            profile_data = {
                'cpf': profile.cpf,
                'birth': profile.birth,
                'phone': profile.phone,
                'email_confirmed': profile.email_confirmed,
                'profile_image_url': profile.get_profile_image_url()
            }
            return profile_data
        except Profile.DoesNotExist:
            return {
                'cpf': None,
                'birth': None, 
                'phone': None,
                'email_confirmed': False,
                'profile_image_url': None
            }