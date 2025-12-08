from rest_framework import permissions, status, parsers, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, inline_serializer
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

# DRF Spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    ProfileImageUploadSerializer, UserWithImageSerializer,
    UserSerializer, ProfileSerializer, UserPermissionsSerializer, RoleAssignmentSerializer,
    UserRegisterSerializer, LoginSerializer, LoginResponseSerializer, AuthResponseSerializer,
    PasswordRecoverySerializer, PasswordRecoveryResponseSerializer, PasswordResetSerializer,
    TokenValidationSerializer, DetailSerializer
)
from users.models import Profile

User = get_user_model()

@extend_schema(
    operation_id="upload_profile_image",
    summary="Upload de imagem de perfil",
    description="Faz upload de uma nova imagem de perfil. A imagem será redimensionada automaticamente para 800x800px mantendo proporção.",
    tags=["Web - User"],
    methods=['POST'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'profile_image': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Arquivo de imagem (JPEG, PNG, WebP - máximo 5MB)'
                }
            },
            'required': ['profile_image']
        }
    },
    responses={
        200: inline_serializer(
            name="UploadProfileImageResponse",
            fields={
                "detail": serializers.CharField(),
                "profile_image_url": serializers.URLField(allow_null=True, required=False),
                "user": UserWithImageSerializer(),
            },
        ),
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
@extend_schema(
    operation_id="delete_profile_image",
    summary="Remover imagem de perfil",
    description="Remove a imagem de perfil atual do usuário.",
    tags=["Web - User"],
    methods=['DELETE'],
    responses={
        200: inline_serializer(
            name="DeleteProfileImageResponse",
            fields={
                "detail": serializers.CharField(),
                "user": UserWithImageSerializer(),
            },
        ),
        404: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Usuário não possui imagem de perfil'}
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
    operation_id="get_user_data", 
    summary="Obter dados completos do usuário",
    description="Retorna dados completos do usuário autenticado incluindo perfil.",
    tags=["Web - User"],
    methods=['GET'],
    responses={200: UserSerializer}
)
@extend_schema(
    operation_id="update_user_data", 
    summary="Atualizar dados do usuário",
    description="Atualiza dados do perfil do usuário autenticado.",
    tags=["Web - User"],
    methods=['PATCH'],
    request=ProfileSerializer,
    responses={200: UserSerializer, 400: DetailSerializer}
)
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    """Retorna dados completos do usuário atual com perfil ou atualiza o perfil"""
    # Garante que o profile existe
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        print(f"DEBUG WEB: Profile criado para usuário: {request.user.username}")
    
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PATCH':
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Retorna dados completos atualizados
            user_serializer = UserSerializer(request.user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    operation_id="get_user_permissions",
    summary="Obter permissões do usuário",
    description="Retorna permissões e grupos do usuário autenticado.",
    tags=["Web - User"],
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
    tags=["Web - User"],
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
    request=UserRegisterSerializer,
    responses={
        201: AuthResponseSerializer,
        400: AuthResponseSerializer,
        500: AuthResponseSerializer
    }
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
    request=None,
    responses={200: AuthResponseSerializer}
)
@api_view(["POST"])
def logout_view(request):
    """Logout do usuário na web"""
    from django.contrib.auth import logout
    logout(request)
    return Response({"detail": "Logout realizado com sucesso"}, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Web - Auth"],
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: AuthResponseSerializer,
        401: AuthResponseSerializer
    }
)
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
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
    request=PasswordRecoverySerializer,
    responses={200: PasswordRecoveryResponseSerializer}
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
    request=PasswordResetSerializer,
    responses={200: AuthResponseSerializer}
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
    responses={200: TokenValidationSerializer}
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


@extend_schema(
    operation_id="serve_profile_image",
    summary="Servir imagem de perfil",
    description="Serve a imagem de perfil como proxy do S3 (alternativa a presigned URLs)",
    tags=["Web - User"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID do usuário"
        )
    ],
    responses={
        200: {
            'description': 'Imagem servida com sucesso',
            'content': {
                'image/jpeg': {},
                'image/png': {},
                'image/webp': {}
            }
        },
        404: {'description': 'Imagem não encontrada'}
    }
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])  # Ou AllowAny se quiser imagens públicas
def serve_profile_image(request, user_id):
    """
    Serve imagem de perfil como proxy do S3
    Alternativa às presigned URLs para maior controle de acesso
    """
    try:
        from django.http import HttpResponse
        from users.services import S3ImageService
        import mimetypes
        
        # Buscar profile do usuário
        profile = Profile.objects.get(user_id=user_id)
        
        if not profile.profile_image:
            return Response(
                {"detail": "Usuário não possui imagem de perfil"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Baixar imagem do S3
        s3_service = S3ImageService()
        
        try:
            response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=profile.profile_image
            )
            
            # Determinar content type baseado na extensão
            content_type, _ = mimetypes.guess_type(profile.profile_image)
            if not content_type:
                content_type = 'image/jpeg'  # fallback
            
            # Retornar imagem como resposta HTTP
            image_data = response['Body'].read()
            
            http_response = HttpResponse(image_data, content_type=content_type)
            http_response['Cache-Control'] = 'public, max-age=3600'  # Cache de 1 hora
            http_response['Content-Length'] = len(image_data)
            
            return http_response
            
        except Exception as e:
            return Response(
                {"detail": f"Erro ao buscar imagem no S3: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Profile.DoesNotExist:
        return Response(
            {"detail": "Usuário não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    summary="Renovar token JWT",
    description="Renova o token de acesso usando o refresh token para aplicação web",
    tags=["Web - User"],
    responses={200: {"type": "object", "properties": {"access": {"type": "string"}}}}
)
class WebTokenRefreshView(TokenRefreshView):
    """View customizada para refresh token com documentação adequada"""
    pass


# ============================================
# Views para gerenciamento de relacionamentos usuário-paciente
# ============================================

@extend_schema(
    summary="Listar meus pacientes",
    description="Lista todos os pacientes atendidos pelo usuário autenticado",
    tags=["Web - User"],
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'relation_id': {'type': 'string', 'format': 'uuid'},
                    'patient_id': {'type': 'string', 'format': 'uuid'},
                    'patient_name': {'type': 'string'},
                    'patient_cpf': {'type': 'string'},
                    'patient_phone': {'type': 'string'},
                    'start_date': {'type': 'string', 'format': 'date-time'},
                    'is_active': {'type': 'boolean'}
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_patients(request):
    """Lista todos os pacientes do usuário autenticado"""
    from users.models import UserPatientRelation
    from .patient_relations_serializers import UserPatientsListSerializer
    
    relations = UserPatientRelation.get_user_patients(request.user, active_only=True)
    serializer = UserPatientsListSerializer(relations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Adicionar paciente aos meus cuidados",
    description="Adiciona um paciente à lista de pacientes atendidos pelo usuário",
    tags=["Web - User"],
    request={"application/json": {
        "type": "object",
        "properties": {
            "patient": {"type": "string", "format": "uuid", "description": "ID do paciente"},
            "notes": {"type": "string", "required": False, "description": "Notas sobre o relacionamento"}
        },
        "required": ["patient"]
    }},
    responses={
        201: {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
                "relation": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "patient_name": {"type": "string"},
                        "start_date": {"type": "string", "format": "date-time"}
                    }
                }
            }
        },
        400: {"type": "object", "properties": {"detail": {"type": "string"}}}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_patient_to_care(request):
    """Adiciona um paciente aos cuidados do usuário autenticado"""
    from .patient_relations_serializers import CreateUserPatientRelationSerializer
    
    serializer = CreateUserPatientRelationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        relation = serializer.save()
        return Response({
            'detail': 'Paciente adicionado aos seus cuidados com sucesso',
            'relation': {
                'id': relation.id,
                'patient_name': relation.patient.full_name,
                'start_date': relation.start_date
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Remover paciente dos meus cuidados",
    description="Remove um paciente da lista de pacientes atendidos (soft delete)",
    tags=["Web - User"],
    responses={
        200: {'type': 'object', 'properties': {'detail': {'type': 'string'}}},
        404: {'type': 'object', 'properties': {'detail': {'type': 'string'}}}
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_patient_from_care(request, relation_id):
    """Remove um paciente dos cuidados do usuário autenticado"""
    from users.models import UserPatientRelation
    
    try:
        relation = UserPatientRelation.objects.get(
            id=relation_id, 
            user=request.user, 
            is_active=True
        )
        relation.deactivate()
        return Response({
            'detail': f'Paciente {relation.patient.full_name} removido dos seus cuidados'
        }, status=status.HTTP_200_OK)
    except UserPatientRelation.DoesNotExist:
        return Response({
            'detail': 'Relacionamento não encontrado ou já inativo'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Listar profissionais que atendem um paciente",
    description="Lista todos os usuários que atendem um paciente específico",
    tags=["Web - User"],
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'relation_id': {'type': 'string', 'format': 'uuid'},
                    'user_id': {'type': 'integer'},
                    'user_name': {'type': 'string'},
                    'user_email': {'type': 'string'},
                    'start_date': {'type': 'string', 'format': 'date-time'},
                    'is_active': {'type': 'boolean'}
                }
            }
        },
        404: {'type': 'object', 'properties': {'detail': {'type': 'string'}}}
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def patient_doctors(request, patient_id):
    """Lista todos os profissionais que atendem um paciente específico"""
    from users.models import UserPatientRelation
    from patients.models import Patient
    from .patient_relations_serializers import PatientDoctorsListSerializer
    
    try:
        patient = Patient.objects.get(id=patient_id, is_active=True)
        relations = UserPatientRelation.get_patient_users(patient, active_only=True)
        serializer = PatientDoctorsListSerializer(relations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Patient.DoesNotExist:
        return Response({
            'detail': 'Paciente não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
