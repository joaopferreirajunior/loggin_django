from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "cpf", "birth", "phone", 
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "clickhouse_id"
        )
        read_only_fields = (
            "email_confirmed", "email_confirmed_at", "invited_at",
            "confirmation_token", "confirmation_sent_at", 
            "recovery_token", "recovery_token_sent_at", "clickhouse_id"
        )

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "profile")
    
    def get_profile(self, obj):
        """Retorna dados do perfil ou cria um vazio se não existir"""
        try:
            return UserProfileSerializer(obj.profile).data
        except UserProfile.DoesNotExist:
            # Cria um profile vazio se não existir
            profile = UserProfile.objects.create(user=obj)
            return UserProfileSerializer(profile).data

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
            if UserProfile.objects.filter(cpf=value).exists():
                raise serializers.ValidationError("Este CPF já está em uso.")
        return value

    def create(self, validated_data):
        # extrai campos do perfil se existirem
        cpf = validated_data.pop('cpf', None)
        birth = validated_data.pop('birth', None)
        phone = validated_data.pop('phone', None)

        user = User.objects.create_user(**validated_data)

        # cria ou atualiza o perfil associado
        try:
            profile = user.profile
            profile.cpf = cpf or profile.cpf
            profile.birth = birth or profile.birth
            profile.phone = phone or profile.phone
            profile.save()
        except Exception:
            # fallback: cria um novo perfil caso não exista
            UserProfile.objects.create(user=user, cpf=cpf or None, birth=birth or None, phone=phone or None)

        return user
