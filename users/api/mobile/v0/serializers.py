# users/api/mobile/v0/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from users.models import Profile
from drf_spectacular.utils import extend_schema_serializer

User = get_user_model()


@extend_schema_serializer(component_name="MobileProfile")
class ProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    # Campos do User para permitir edição junto com o profile
    email = serializers.EmailField(source='user.email', help_text="Email do usuário")
    first_name = serializers.CharField(source='user.first_name', help_text="Nome do usuário", max_length=150, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', help_text="Sobrenome do usuário", max_length=150, allow_blank=True)
    
    class Meta:
        model = Profile
        fields = (
            "first_name", "last_name", "cpf", "birth", "phone", "email",
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "legacy_id",
            "factory_mode", "profile_image_url"
        )
        read_only_fields = (
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "legacy_id",
            "factory_mode", "profile_image_url"
        )
    
    def get_profile_image_url(self, obj) -> str:
        """Retorna URL completa da imagem de perfil do S3"""
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


@extend_schema_serializer(component_name="MobileUser")
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    # Campos adicionais para exibição
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "full_name", "profile", "permissions")
    
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


@extend_schema_serializer(component_name="MobileUserRegisterRequest")
class UserRegisterSerializer(serializers.ModelSerializer):
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
        fields = ["username", "email", "password", "first_name", "last_name", "cpf", "birth", "phone"]

    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError(
                "O nome de usuário só pode conter letras e números."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Formato de e-mail inválido.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return value

    def validate_cpf(self, value):
        # validação simples: se informado, garante unicidade
        if value:
            if Profile.objects.filter(cpf=value).exists():
                raise serializers.ValidationError("Este CPF já está em uso.")
        return value

    def create(self, validated_data):
        # extrai campos do perfil
        cpf = validated_data.pop("cpf")
        birth = validated_data.pop("birth", None)
        phone = validated_data.pop("phone", None)

        user = User.objects.create_user(**validated_data)

        # Atualizar profile criado pelo signal com dados adicionais
        # Usa get_or_create para garantir que o profile existe (proteção contra race condition)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.cpf = cpf
        profile.birth = birth
        profile.phone = phone
        profile.save()

        return user


# --- Schemas genéricos de mensagens/erros ---


@extend_schema_serializer(component_name="MobileDetail")
class DetailSerializer(serializers.Serializer):
    """Usado para mensagens simples: {"detail": "..."}"""

    detail = serializers.CharField()


# --- Auth / Registro / Login ---


@extend_schema_serializer(component_name="MobileRegisterResponse")
class RegisterResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = UserSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()


@extend_schema_serializer(component_name="MobileLoginRequest")
class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        help_text="Pode ser username ou email",
    )
    password = serializers.CharField()


@extend_schema_serializer(component_name="MobileLoginResponse")
class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()


# --- Recuperação de senha ---


@extend_schema_serializer(component_name="MobileRecoveryPasswordRequest")
class RecoveryPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


@extend_schema_serializer(component_name="MobileRecoveryPasswordResponse")
class RecoveryPasswordResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    test_link = serializers.CharField()
    test_token = serializers.CharField()


@extend_schema_serializer(component_name="MobileResetPasswordRequest")
class ResetPasswordRequestSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()


@extend_schema_serializer(component_name="MobileResetPasswordSuccess")
class ResetPasswordSuccessSerializer(serializers.Serializer):
    detail = serializers.CharField()


# --- Permissões / papéis de usuário ---


@extend_schema_serializer(component_name="MobileUserPermissions")
class UserPermissionsSerializer(serializers.Serializer):
    user_role = serializers.CharField()
    is_system_admin = serializers.BooleanField()
    is_office_admin = serializers.BooleanField()
    is_regular_user = serializers.BooleanField()
    roles = serializers.ListField(child=serializers.CharField())
    permissions = serializers.ListField(child=serializers.CharField())
    can_manage_users = serializers.BooleanField()
    can_view_all_users = serializers.BooleanField()
    can_access_admin = serializers.BooleanField()


@extend_schema_serializer(component_name="MobileAssignUserRoleRequest")
class AssignUserRoleRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=["system_admin", "office_admin", "regular_user"],
    )


@extend_schema_serializer(component_name="MobileAssignUserRoleResponse")
class AssignUserRoleResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = serializers.CharField()
    role = serializers.CharField()


@extend_schema_serializer(component_name="MobileProfileImageUpload")
class MobileProfileImageUploadSerializer(serializers.Serializer):
    """
    Serializer para upload de imagem de perfil mobile
    """
    profile_image = serializers.ImageField(
        required=True,
        help_text="Imagem de perfil (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_profile_image(self, value):
        """
        Valida a imagem usando o serviço S3ImageService
        """
        from users.services import S3ImageService
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
            from users.services import S3ImageService
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
            print(f"Erro completo no upload mobile: {traceback.format_exc()}")
            raise serializers.ValidationError(f"Erro interno no upload: {str(e)}")


@extend_schema_serializer(component_name="MobileUserWithImage")
class MobileUserWithImageSerializer(serializers.ModelSerializer):
    """
    Serializer do usuário mobile incluindo URL da imagem de perfil
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
