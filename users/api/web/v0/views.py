from rest_framework import permissions, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt

# DRF Spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    ProfileImageUploadSerializer, UserWithImageSerializer,
    UserSerializer, ProfileSerializer, UserPermissionsSerializer, RoleAssignmentSerializer,
    UserRegisterSerializer
)
from users.models import Profile

User = get_user_model()

@extend_schema(
    operation_id="manage_profile_image",
    summary="Gerenciar imagem de perfil",
    description="Upload (POST) ou remove (DELETE) imagem de perfil. A imagem será redimensionada automaticamente para 800x800px mantendo proporção.",
    tags=["User Management"],
    methods=['POST', 'DELETE'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'profile_image': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo de imagem (JPEG, PNG, WebP - máximo 5MB) - apenas para POST'
                }
            },
            'required': ['profile_image']
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Imagem de perfil atualizada/removida com sucesso'},
                'profile_image_url': {'type': 'string', 'example': 'https://bucket.s3.region.amazonaws.com/profiles/user_1/avatar.jpg'},
                'user': UserWithImageSerializer
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Erro de validação da imagem'}
            }
        },
        401: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Token de autenticação necessário'}
            }
        }
    }
)
@csrf_exempt
@api_view(['POST', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([parsers.MultiPartParser, parsers.FormParser])
def manage_profile_image(request):
    """
    Gerencia upload e remoção da imagem de perfil
    """
    if request.method == 'POST':
        # Upload da imagem
        serializer = ProfileImageUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Salva a imagem e atualiza o profile
                profile = serializer.save(user=request.user)
                
                # Retorna dados atualizados do usuário
                user_serializer = UserWithImageSerializer(request.user)
                
                return Response({
                    'detail': 'Imagem de perfil atualizada com sucesso',
                    'profile_image_url': profile.get_profile_image_url(),
                    'user': user_serializer.data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'detail': f'Erro interno ao processar imagem: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Remoção da imagem
        try:
            profile = request.user.profile
            
            if not profile.profile_image:
                return Response({
                    'detail': 'Usuário não possui imagem de perfil'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Remove imagem do S3 e limpa campo
            success = profile.delete_profile_image()
            
            if success:
                # Retorna dados atualizados do usuário
                user_serializer = UserWithImageSerializer(request.user)
                
                return Response({
                    'detail': 'Imagem de perfil removida com sucesso',
                    'user': user_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'detail': 'Erro ao remover imagem do S3'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Profile.DoesNotExist:
            return Response({
                'detail': 'Profile do usuário não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

@extend_schema(
    operation_id="get_current_user",
    summary="Obter dados do usuário atual",
    description="Retorna dados básicos do usuário autenticado.",
    tags=["User Management"],
    responses={200: UserSerializer}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    """Retorna dados básicos do usuário atual"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    operation_id="get_current_user_profile", 
    summary="Obter perfil completo do usuário",
    description="Retorna dados completos do perfil do usuário autenticado.",
    tags=["User Management"],
    responses={200: ProfileSerializer}
)
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user_profile(request):
    """Retorna ou atualiza dados do perfil do usuário atual"""
    if request.method == 'GET':
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = Profile.objects.create(user=request.user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    operation_id="get_user_permissions",
    summary="Obter permissões do usuário",
    description="Retorna permissões e grupos do usuário autenticado.",
    tags=["User Management"],
    responses={200: UserPermissionsSerializer}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_permissions(request):
    """Retorna permissões do usuário atual"""
    serializer = UserPermissionsSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    operation_id="assign_role",
    summary="Atribuir role ao usuário",
    description="Permite alterar o grupo/role de um usuário (apenas para administradores).",
    tags=["User Management"],
    request=RoleAssignmentSerializer,
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_role(request):
    """Atribui role a um usuário (apenas administradores)"""
    serializer = RoleAssignmentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save(current_user=request.user)
            return Response({"detail": result}, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Views de autenticação para web

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Cadastro de novos usuários na web"""
    try:
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Para web, retorna sucesso simples
            return Response({
                "detail": "Conta criada com sucesso!",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"detail": f"Erro interno do servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@api_view(["POST"])
def logout_view(request):
    """Logout do usuário na web"""
    from django.contrib.auth import logout
    logout(request)
    return Response({"detail": "Logout realizado com sucesso"}, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Login de usuários na web"""
    from django.contrib.auth import authenticate, login
    from rest_framework_simplejwt.tokens import RefreshToken
    
    username_or_email = request.data.get("username")
    password = request.data.get("password")
    
    # Validações básicas
    if not username_or_email:
        return Response(
            {"detail": "Username ou email é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    if not password:
        return Response(
            {"detail": "Senha é obrigatória"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verifica se é email ou username
    if "@" in username_or_email:
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response(
                {"detail": "Email não encontrado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        username = username_or_email

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        
        # Gera tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "detail": "Login realizado com sucesso",
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {"detail": "Credenciais inválidas"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def recovery_password(request):
    """Recuperação de senha por email"""
    email = request.data.get("email")
    
    if not email:
        return Response(
            {"detail": "Email é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Gera token de recuperação
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        recovery_token = "".join(secrets.choice(alphabet) for _ in range(32))
        
        # Salva o token
        from django.utils import timezone
        profile.recovery_token = recovery_token
        profile.recovery_token_sent_at = timezone.now()
        profile.save()
        
        # Envia email (simulado)
        return Response({
            "detail": f"Se o email {email} estiver registrado, você receberá instruções para recuperação de senha.",
            "test_token": recovery_token  # Apenas para desenvolvimento
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        # Retorna mesmo resultado por segurança
        return Response({
            "detail": f"Se o email {email} estiver registrado, você receberá instruções para recuperação de senha."
        }, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset de senha usando token"""
    token = request.data.get("token")
    new_password = request.data.get("password")

    if not token or not new_password:
        return Response(
            {"detail": "Token e nova senha são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 8:
        return Response(
            {"detail": "A senha deve ter pelo menos 8 caracteres"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        profile = Profile.objects.get(recovery_token=token)
        
        # Verifica se token não expirou (24h)
        from django.utils import timezone
        from datetime import timedelta
        if profile.recovery_token_sent_at and (timezone.now() - profile.recovery_token_sent_at) > timedelta(hours=24):
            return Response(
                {"detail": "Token expirado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Atualiza senha
        profile.user.set_password(new_password)
        profile.user.save()
        
        # Limpa token
        profile.recovery_token = None
        profile.recovery_token_sent_at = None
        profile.save()
        
        return Response({
            "detail": "Senha alterada com sucesso!"
        }, status=status.HTTP_200_OK)
        
    except Profile.DoesNotExist:
        return Response(
            {"detail": "Token inválido"},
            status=status.HTTP_400_BAD_REQUEST,
        )

@extend_schema(
    tags=["Web - Auth"],
    responses={200: {"type": "object", "properties": {"valid": {"type": "boolean"}}}}
)
@api_view(["GET"])
@permission_classes([AllowAny])
def validate_token(request):
    """Valida token de recuperação"""
    token = request.GET.get("token")
    
    if not token:
        return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)

    try:
        profile = Profile.objects.get(recovery_token=token)
        
        # Verifica se token não expirou
        from django.utils import timezone
        from datetime import timedelta
        if profile.recovery_token_sent_at and (timezone.now() - profile.recovery_token_sent_at) > timedelta(hours=24):
            return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"valid": True}, status=status.HTTP_200_OK)
        
    except Profile.DoesNotExist:
        return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)
