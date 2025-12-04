from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from users.models import Profile


User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = (
            "cpf", "birth", "phone", 
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "clickhouse_id",
            "profile_image_url"
        )
        read_only_fields = (
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "clickhouse_id",
            "profile_image_url"
        )
    
    def get_profile_image_url(self, obj):
        """Retorna URL completa da imagem de perfil do S3"""
        return obj.get_profile_image_url()

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "profile")
    

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    email = serializers.EmailField(required=True)
    # campos adicionais para o perfil
    cpf = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    birth = serializers.DateField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'cpf', 'birth', 'phone']

    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("O nome de usuário só pode conter letras e números.")
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
        # extrai campos do perfil se existirem
        cpf = validated_data.pop('cpf', None)
        birth = validated_data.pop('birth', None)
        phone = validated_data.pop('phone', None)

        user = User.objects.create_user(**validated_data)

        # aguarda o signal criar o profile, então atualiza com os dados extras
        try:
            # usa get_or_create para evitar conflitos com o signal
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'cpf': cpf,
                    'birth': birth,
                    'phone': phone
                }
            )
            # se o profile já existia (criado pelo signal), atualiza os campos
            if not created:
                if cpf:
                    profile.cpf = cpf
                if birth:
                    profile.birth = birth
                if phone:
                    profile.phone = phone
                profile.save()
        except Exception as e:
            # log do erro para debug
            print(f"Erro ao criar/atualizar perfil do usuário {user.username}: {e}")
            # se falhar, o usuário ainda existe, só não terá o perfil completo

        return user

# --- Schemas genéricos de mensagens/erros ---


class DetailSerializer(serializers.Serializer):
    """Usado para mensagens simples: {"detail": "..."}"""
    detail = serializers.CharField()


# --- Auth / Registro / Login ---


class RegisterResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = UserSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(
        help_text="Pode ser username ou email"
    )
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()


# --- Recuperação de senha ---


class RecoveryPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RecoveryPasswordResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    test_link = serializers.CharField()
    test_token = serializers.CharField()


class ResetPasswordRequestSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()


class ResetPasswordSuccessSerializer(serializers.Serializer):
    detail = serializers.CharField()


# --- Permissões / papéis de usuário ---


class UserPermissionsSerializer(serializers.Serializer):
    user_role = serializers.CharField()
    is_system_admin = serializers.BooleanField()
    is_office_admin = serializers.BooleanField()
    is_regular_user = serializers.BooleanField()
    groups = serializers.ListField(
        child=serializers.CharField()
    )
    permissions = serializers.ListField(
        child=serializers.CharField()
    )
    can_manage_users = serializers.BooleanField()
    can_view_all_users = serializers.BooleanField()
    can_access_admin = serializers.BooleanField()


class AssignUserRoleRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=["system_admin", "office_admin", "regular_user"]
    )


class AssignUserRoleResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    user = serializers.CharField()
    role = serializers.CharField()