# users/api/legacy/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse
from users.models import Profile
from .serializers import (
    LegacyUserInputSerializer,
    LegacyUserBatchInputSerializer,
    LegacyUserOutputSerializer,
    LegacySyncResponseSerializer,
    DetailSerializer,
)

User = get_user_model()


def validate_legacy_token(request):
    """
    Valida o token de autenticação do sistema legado.
    Retorna True se o token é válido, False caso contrário.
    """
    auth_header = request.headers.get('Authorization', '')
    
    # Espera formato: "Bearer <token>" ou apenas "<token>"
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        token = auth_header
    
    expected_token = getattr(settings, 'LEGACY_API_TOKEN', None)
    
    if not expected_token:
        return False
    
    return token == expected_token


def create_or_update_user(user_data):
    """
    Cria ou atualiza um usuário com base no email.
    Retorna um dicionário com o resultado da operação.
    
    Args:
        user_data: Dicionário com os dados do usuário validados
    
    Returns:
        dict: {
            'id': int,
            'email': str,
            'username': str,
            'created': bool,
            'message': str,
            'success': bool
        }
    """
    try:
        email = user_data.get('email')
        
        # Gera username a partir do email se não fornecido
        username = user_data.get('username')
        if not username or username.strip() == '':
            username = email.split('@')[0]
        
        # Tenta buscar usuário por email
        try:
            user = User.objects.get(email=email)
            created = False
            
            # Atualiza dados do User
            user.username = username
            user.first_name = user_data.get('first_name', '')
            user.last_name = user_data.get('last_name', '')
            user.save()
            
            # Atualiza Profile (deve existir por causa do signal)
            profile = user.profile
            profile.cpf = user_data.get('cpf')
            profile.birth = user_data.get('birth')
            profile.phone = user_data.get('phone')
            profile.legacy_id = user_data.get('legacy_id')
            profile.invited_at = user_data.get('invited_at')
            
            # Se email_confirmed_at vier preenchido, marca email como confirmado
            email_confirmed_at = user_data.get('email_confirmed_at')
            if email_confirmed_at:
                profile.email_confirmed = True
                profile.email_confirmed_at = email_confirmed_at
            
            # Armazena dados legados adicionais no scratchpad se fornecidos
            if 'legacy_data' in user_data and user_data['legacy_data']:
                profile.scratchpad['legacy_data'] = user_data['legacy_data']
            
            profile.save()
            
            message = f"Usuário {email} atualizado com sucesso"
            
        except User.DoesNotExist:
            # Cria novo usuário
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                )
                
                # O Profile é criado automaticamente pelo signal
                # Mas vamos buscar e atualizar com os dados adicionais
                profile = user.profile
                profile.cpf = user_data.get('cpf')
                profile.birth = user_data.get('birth')
                profile.phone = user_data.get('phone')
                profile.legacy_id = user_data.get('legacy_id')
                profile.invited_at = user_data.get('invited_at')
                
                # Se email_confirmed_at vier preenchido, marca email como confirmado
                email_confirmed_at = user_data.get('email_confirmed_at')
                if email_confirmed_at:
                    profile.email_confirmed = True
                    profile.email_confirmed_at = email_confirmed_at
                
                # Armazena dados legados adicionais no scratchpad se fornecidos
                if 'legacy_data' in user_data and user_data['legacy_data']:
                    profile.scratchpad['legacy_data'] = user_data['legacy_data']
                
                profile.save()
            
            created = True
            message = f"Usuário {email} criado com sucesso"
        
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'created': created,
            'message': message,
            'success': True
        }
        
    except Exception as e:
        return {
            'id': None,
            'email': user_data.get('email', 'unknown'),
            'username': user_data.get('username', 'unknown'),
            'created': False,
            'message': f"Erro ao processar usuário: {str(e)}",
            'success': False
        }


@extend_schema(
    tags=["Legacy - User"],
    request=LegacyUserBatchInputSerializer,
    responses={
        200: LegacySyncResponseSerializer,
        401: OpenApiResponse(
            response=DetailSerializer,
            description="Token de autenticação inválido ou ausente",
        ),
        400: OpenApiResponse(
            response=DetailSerializer,
            description="Erros de validação dos dados recebidos",
        ),
    },
    description="Endpoint para sincronização em lote de usuários do sistema legado. "
                "Recebe um array de usuários e cria ou atualiza cada um com base no email.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def legacy_sync_users(request):
    """
    Sincroniza lote de usuários do sistema legado.
    Cria novos usuários ou atualiza existentes com base no email.
    """
    # Valida token de autenticação
    if not validate_legacy_token(request):
        return Response(
            {"detail": "Token de autenticação inválido ou ausente"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Valida dados recebidos
    serializer = LegacyUserBatchInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    users_data = serializer.validated_data['users']
    
    # Processa cada usuário
    results = []
    errors = []
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    for user_data in users_data:
        result = create_or_update_user(user_data)
        
        if result['success']:
            results.append({
                'id': result['id'],
                'email': result['email'],
                'username': result['username'],
                'created': result['created'],
                'message': result['message']
            })
            
            if result['created']:
                total_created += 1
            else:
                total_updated += 1
        else:
            total_errors += 1
            errors.append({
                'email': result['email'],
                'error': result['message']
            })
    
    # Monta resposta
    response_data = {
        'total_received': len(users_data),
        'total_created': total_created,
        'total_updated': total_updated,
        'total_errors': total_errors,
        'results': results,
        'errors': errors
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Legacy - User"],
    request=LegacyUserInputSerializer,
    responses={
        200: LegacyUserOutputSerializer,
        401: OpenApiResponse(
            response=DetailSerializer,
            description="Token de autenticação inválido ou ausente",
        ),
        400: OpenApiResponse(
            response=DetailSerializer,
            description="Erros de validação dos dados recebidos",
        ),
    },
    description="Endpoint para criar ou atualizar um único usuário (usado pelos triggers do sistema legado). "
                "Identifica o usuário pelo email e cria se não existir ou atualiza se já existir.",
)
@api_view(['POST'])
@permission_classes([AllowAny])
def legacy_upsert_user(request):
    """
    Cria ou atualiza um único usuário (endpoint para triggers).
    Identifica pelo email - cria se não existir, atualiza se existir.
    """
    # Valida token de autenticação
    if not validate_legacy_token(request):
        return Response(
            {"detail": "Token de autenticação inválido ou ausente"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Valida dados recebidos
    serializer = LegacyUserInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Processa o usuário
    result = create_or_update_user(serializer.validated_data)
    
    if result['success']:
        return Response(
            {
                'id': result['id'],
                'email': result['email'],
                'username': result['username'],
                'created': result['created'],
                'message': result['message']
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"detail": result['message']},
            status=status.HTTP_400_BAD_REQUEST
        )
