# users/api/legacy/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.models import Profile
from drf_spectacular.utils import extend_schema_serializer

User = get_user_model()


@extend_schema_serializer(component_name="LegacyUserInput")
class LegacyUserInputSerializer(serializers.Serializer):
    """
    Serializer para receber dados de usuário do sistema legado.
    Este é o formato que o sistema legado deve enviar.
    """
    email = serializers.EmailField(required=True, help_text="Email do usuário (identificador único)")
    username = serializers.CharField(required=False, allow_blank=True, max_length=150, help_text="Nome de usuário (gerado a partir do email se não fornecido)")
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150, help_text="Nome do usuário")
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150, help_text="Sobrenome do usuário")
    
    # Campos do Profile
    cpf = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=14, help_text="CPF do usuário")
    birth = serializers.DateField(required=False, allow_null=True, help_text="Data de nascimento")
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20, help_text="Telefone")
    legacy_id = serializers.UUIDField(required=False, allow_null=True, help_text="UUID do usuário no sistema legado")
    email_confirmed_at = serializers.DateTimeField(required=False, allow_null=True, help_text="Data/hora de confirmação do email no sistema legado")
    invited_at = serializers.DateTimeField(required=False, allow_null=True, help_text="Data/hora do convite no sistema legado")
    
    # Campos opcionais para mapeamento futuro
    legacy_data = serializers.JSONField(required=False, allow_null=True, help_text="Dados adicionais do sistema legado para mapeamento futuro")


@extend_schema_serializer(component_name="LegacyUserBatchInput")
class LegacyUserBatchInputSerializer(serializers.Serializer):
    """
    Serializer para receber lote de usuários do sistema legado.
    """
    users = serializers.ListField(
        child=LegacyUserInputSerializer(),
        required=True,
        help_text="Lista de usuários a serem sincronizados"
    )


@extend_schema_serializer(component_name="LegacyUserOutput")
class LegacyUserOutputSerializer(serializers.Serializer):
    """
    Serializer de resposta para operações da API legacy.
    """
    id = serializers.IntegerField(help_text="ID do usuário no sistema")
    email = serializers.EmailField(help_text="Email do usuário")
    username = serializers.CharField(help_text="Nome de usuário")
    created = serializers.BooleanField(help_text="Indica se o usuário foi criado (True) ou atualizado (False)")
    message = serializers.CharField(help_text="Mensagem descritiva da operação")


@extend_schema_serializer(component_name="LegacySyncResponse")
class LegacySyncResponseSerializer(serializers.Serializer):
    """
    Serializer de resposta para a operação de sync em lote.
    """
    total_received = serializers.IntegerField(help_text="Total de usuários recebidos")
    total_created = serializers.IntegerField(help_text="Total de usuários criados")
    total_updated = serializers.IntegerField(help_text="Total de usuários atualizados")
    total_errors = serializers.IntegerField(help_text="Total de erros encontrados")
    results = serializers.ListField(
        child=LegacyUserOutputSerializer(),
        help_text="Lista de resultados detalhados por usuário"
    )
    errors = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de erros encontrados durante o processamento"
    )


@extend_schema_serializer(component_name="DetailSerializer")
class DetailSerializer(serializers.Serializer):
    """
    Serializer genérico para mensagens de erro.
    """
    detail = serializers.CharField(help_text="Mensagem de erro ou informação")
