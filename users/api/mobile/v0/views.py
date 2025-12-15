# users/api/mobile/v0/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authentication import SessionAuthentication
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from datetime import timedelta
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from users.models import Profile
import secrets
import string

from users.models import Profile

from .serializers import (
    UserRegisterSerializer,
    UserSerializer,
    ProfileSerializer,
    DetailSerializer,
    RegisterResponseSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    RecoveryPasswordRequestSerializer,
    RecoveryPasswordResponseSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordSuccessSerializer,
    UserPermissionsSerializer,
    AssignUserRoleRequestSerializer,
    AssignUserRoleResponseSerializer,
)

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)


@extend_schema(
    tags=["Mobile - Auth"],
    request=UserRegisterSerializer,
    responses={
        201: RegisterResponseSerializer,
        400: OpenApiResponse(
            response=DetailSerializer,
            description="Erros de validação do cadastro",
        ),
        500: OpenApiResponse(
            response=DetailSerializer,
            description="Erro interno do servidor",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def register(request):
    try:
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"DEBUG MOBILE: Usuário {user.username} criado com sucesso")

            # Gera tokens JWT para o novo usuário
            refresh = RefreshToken.for_user(user)
            user_serializer = UserSerializer(user)

            return Response(
                {
                    "detail": "Conta criada com sucesso!",
                    "user": user_serializer.data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            print(
                f"DEBUG MOBILE: Erros de validação no registro: {serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        print(f"DEBUG MOBILE: Erro interno no registro: {str(e)}")
        import traceback

        traceback.print_exc()
        return Response(
            {"detail": f"Erro interno do servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Mobile - Auth"],
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        401: OpenApiResponse(
            response=DetailSerializer,
            description="Credenciais inválidas ou email não encontrado",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    username_or_email = request.data.get("username")
    password = request.data.get("password")

    print(f"DEBUG MOBILE: Tentativa de login com: '{username_or_email}'")
    print(f"DEBUG MOBILE: Request headers: {request.headers}")

    # Primeiro, verifica se é um email válido
    if "@" in (username_or_email or ""):
        # É um email, tenta encontrar o usuário por email
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
            print(
                f"DEBUG MOBILE: Email '{username_or_email}' encontrado, username: '{username}'"
            )
        except User.DoesNotExist:
            print(
                f"DEBUG MOBILE: Email '{username_or_email}' não encontrado"
            )
            return Response(
                {"detail": "Email não encontrado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        # É um username
        username = username_or_email
        print(f"DEBUG MOBILE: Usando como username: '{username}'")

    user = authenticate(username=username, password=password)
    print(f"DEBUG MOBILE: Resultado da autenticação: {user}")

    if user is not None:
        login(request, user)
        print(
            f"DEBUG MOBILE: Login realizado com sucesso para usuário: {user.username}"
        )

        # Gera tokens JWT
        refresh = RefreshToken.for_user(user)

        # Retorna os dados completos do usuário com tokens
        serializer = UserSerializer(user)
        return Response(
            {
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
    else:
        print(
            f"DEBUG MOBILE: Falha na autenticação para username: '{username}'"
        )
        return Response(
            {"detail": "Credenciais inválidas"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@extend_schema(
    tags=["Mobile - Auth"],
    request=None,
    responses={
        200: DetailSerializer,
    },
)
@api_view(["POST"])
@csrf_exempt
def logout_view(request):
    logout(request)
    return Response(
        {"detail": "Logout realizado com sucesso"},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Mobile - Auth"],
    request=RecoveryPasswordRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=RecoveryPasswordResponseSerializer,
            description=(
                "Mensagem genérica de sucesso. "
                "Em ambiente de desenvolvimento pode retornar test_link e test_token."
            ),
        ),
        400: OpenApiResponse(
            response=DetailSerializer,
            description="Email é obrigatório",
        ),
        500: OpenApiResponse(
            response=DetailSerializer,
            description="Erro interno do servidor",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def recovery_password(request):
    """
    Endpoint para solicitar recuperação de senha via email.
    Recebe email do usuário e envia token de recuperação.
    """
    email = request.data.get("email")

    if not email:
        return Response(
            {"detail": "Email é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    print(f"DEBUG MOBILE: Solicitação de recuperação de senha para: {email}")

    try:
        # Busca o usuário pelo email
        user = User.objects.get(email=email)
        print(f"DEBUG MOBILE: Usuário encontrado: {user.username}")

        # Garante que o profile existe
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            print(
                f"DEBUG MOBILE: Profile criado para usuário: {user.username}"
            )

        # Gera token de recuperação (string aleatória segura)
        recovery_token = generate_recovery_token()
        print(f"DEBUG MOBILE: Token gerado: {recovery_token[:10]}...")

        # Salva o token e timestamp no profile
        profile.recovery_token = recovery_token
        profile.recovery_token_sent_at = timezone.now()
        profile.save()

        # Envia email de recuperação
        try:
            send_recovery_email(user, email, recovery_token)
            print(
                f"DEBUG MOBILE: Email de recuperação enviado para: {email}"
            )
        except Exception as email_error:
            print(f"DEBUG MOBILE: Erro ao enviar email: {email_error}")
            # Mesmo se o email falhar, não revelamos isso ao usuário por segurança

        # Para fins de teste, retorna o link de validação
        validation_link = (
            f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')}"
            f"/api/mobile/v0/validatetoken/?token={recovery_token}"
        )

        return Response(
            {
                "detail": (
                    f"Se o email {email} estiver registrado, você receberá "
                    f"instruções para recuperação de senha."
                ),
                "test_link": validation_link,  # APENAS PARA DESENVOLVIMENTO
                "test_token": recovery_token,  # APENAS PARA DESENVOLVIMENTO
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        print(f"DEBUG MOBILE: Email não encontrado: {email}")
        # Por segurança, sempre retorna a mesma mensagem
        return Response(
            {
                "detail": (
                    f"Se o email {email} estiver registrado, você receberá "
                    f"instruções para recuperação de senha."
                )
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(f"DEBUG MOBILE: Erro interno na recuperação: {e}")
        return Response(
            {"detail": "Erro interno do servidor"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def generate_recovery_token():
    """Gera token seguro de 32 caracteres para recuperação de senha"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))


def send_recovery_email(user, email, token):
    """Envia email com link de recuperação de senha"""
    subject = "Recuperação de Senha - Medical San"

    # URL para validar token (que redirecionará para reset se válido)
    validate_url = (
        f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')}"
        f"/api/mobile/v0/validatetoken/?token={token}"
    )

    message = f"""
    Olá {user.username},

    Você solicitou a recuperação da sua senha.

    Clique no link abaixo para redefinir sua senha:
    {validate_url}

    Este link é válido por 24 horas.

    Se você não solicitou esta recuperação, ignore este email.

    Atenciosamente,
    Equipe Medical San
    """

    # Envia o email
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            "noreply@medicalsan.com",
        ),
        recipient_list=[email],
        fail_silently=False,  # Para debug, depois pode mudar para True
    )


@extend_schema(
    tags=["Mobile - Auth"],
    request=ResetPasswordRequestSerializer,
    responses={
        200: ResetPasswordSuccessSerializer,
        400: OpenApiResponse(
            response=DetailSerializer,
            description=(
                "Token inválido/expirado ou problemas como senha curta, "
                "token ausente, etc."
            ),
        ),
        500: OpenApiResponse(
            response=DetailSerializer,
            description="Erro interno do servidor",
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def reset_password(request):
    """
    Endpoint para resetar senha usando token de recuperação.
    Recebe token e nova senha, valida e atualiza a senha do usuário.
    """
    token = request.data.get("token")
    new_password = request.data.get("password")

    if not token:
        return Response(
            {"detail": "Token é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not new_password:
        return Response(
            {"detail": "Nova senha é obrigatória"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 8:
        return Response(
            {"detail": "A senha deve ter pelo menos 8 caracteres"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    print(f"DEBUG MOBILE: Tentativa de reset com token: {token[:10]}...")

    try:
        # Busca o profile com o token
        profile = Profile.objects.get(recovery_token=token)
        user = profile.user

        print(
            f"DEBUG MOBILE: Token encontrado para usuário: {user.username}"
        )

        # Verifica se o token não expirou (24 horas)
        if not is_token_valid(profile):
            print(
                f"DEBUG MOBILE: Token expirado para usuário: {user.username}"
            )
            return Response(
                {
                    "detail": (
                        "Token de recuperação expirado. "
                        "Solicite uma nova recuperação de senha."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Atualiza a senha do usuário
        user.set_password(new_password)
        user.save()

        # Limpa o token de recuperação (uso único)
        profile.recovery_token = None
        profile.recovery_token_sent_at = None
        profile.save()

        print(
            f"DEBUG MOBILE: Senha alterada com sucesso para usuário: {user.username}"
        )

        return Response(
            {
                "detail": (
                    "Senha alterada com sucesso! Você pode fazer login com sua nova senha."
                )
            },
            status=status.HTTP_200_OK,
        )

    except Profile.DoesNotExist:
        print(
            f"DEBUG MOBILE: Token não encontrado: {token[:10]}..."
        )
        return Response(
            {
                "detail": "Token de recuperação inválido ou expirado",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        print(f"DEBUG MOBILE: Erro interno no reset de senha: {e}")
        return Response(
            {"detail": "Erro interno do servidor"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def is_token_valid(profile):
    """
    Verifica se o token de recuperação ainda é válido (não expirou).
    Token é válido por 24 horas após o envio.
    """
    if not profile.recovery_token or not profile.recovery_token_sent_at:
        return False

    # Calcula a diferença de tempo
    now = timezone.now()
    token_age = now - profile.recovery_token_sent_at

    # Token válido por 24 horas
    return token_age < timedelta(hours=24)


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def validate_token(request):
    """
    Endpoint para validar token de recuperação via GET.
    GET /api/mobile/v0/validatetoken/?token=abc123token

    Se token válido: redireciona para /reset-password/?token=abc123token
    Se token inválido: redireciona para /recovery-password/ com erro
    """
    token = request.GET.get("token")

    if not token:
        # Redireciona para página de recuperação com erro
        return redirect("/recovery-password/?error=token_missing")

    try:
        profile = Profile.objects.get(recovery_token=token)

        if is_token_valid(profile):
            # Token válido - redireciona para página de reset com token
            print(
                f"DEBUG MOBILE: Token válido para usuário: {profile.user.username}"
            )
            return redirect(f"/reset-password/?token={token}")
        else:
            # Token expirado
            print(
                f"DEBUG MOBILE: Token expirado para usuário: {profile.user.username}"
            )
            return redirect("/recovery-password/?error=token_expired")

    except Profile.DoesNotExist:
        # Token não encontrado
        print(
            f"DEBUG MOBILE: Token não encontrado: {token[:10]}..."
        )
        return redirect("/recovery-password/?error=token_invalid")
    except Exception as e:
        print(f"DEBUG MOBILE: Erro na validação do token: {e}")
        return redirect("/recovery-password/?error=server_error")


# Retorna os dados completos do próprio usuário logado
@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - User"],
        responses={200: ProfileSerializer, 500: DetailSerializer},
    ),
    patch=extend_schema(
        tags=["Mobile - User"],
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 500: DetailSerializer},
    ),
)
# Retorna os dados de auth_user do próprio usuário logado
@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - User"],
        responses={200: UserSerializer, 500: DetailSerializer},
    ),
    patch=extend_schema(
        tags=["Mobile - User"],
        request=ProfileSerializer,
        responses={200: UserSerializer, 400: DetailSerializer, 500: DetailSerializer},
    ),
)
class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retorna os dados completos do próprio usuário logado com perfil."""
        try:
            # Garante que o profile existe
            profile, created = Profile.objects.get_or_create(user=request.user)
            if created:
                print(f"DEBUG MOBILE: Profile criado para usuário: {request.user.username}")
            
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            print(f"DEBUG MOBILE: Erro em MeView.get: {e}")
            return Response(
                {"detail": f"Erro ao buscar dados do usuário: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def patch(self, request):
        """Atualiza dados do perfil do usuário atual."""
        try:
            # Garante que o profile existe
            profile, created = Profile.objects.get_or_create(user=request.user)
            if created:
                print(f"DEBUG MOBILE: Profile criado para usuário: {request.user.username}")
            
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Retorna dados completos atualizados
                user_serializer = UserSerializer(request.user)
                return Response(user_serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"DEBUG MOBILE: Erro em MeView.patch: {e}")
            return Response(
                {"detail": f"Erro ao atualizar perfil: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# View para gerenciar permissões e roles de usuário
@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - User"],
        responses={200: UserPermissionsSerializer, 500: DetailSerializer},
    ),
)
class UserPermissionsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retorna as permissões e role do usuário atual"""
        try:
            user = request.user
            profile = user.profile

            # Dados do usuário e permissões
            user_data = {
                "user_role": profile.get_user_role(),
                "is_system_admin": profile.is_system_admin(),
                "is_office_admin": profile.is_office_admin(),
                "is_regular_user": profile.is_regular_user(),
                "roles": [group.name for group in user.groups.all()],
                "permissions": list(user.get_all_permissions()),
                "can_manage_users": profile.can_manage_users(),
                "can_view_all_users": profile.can_view_all_users(),
                "can_access_admin": profile.can_access_admin(),
            }

            return Response(user_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"DEBUG MOBILE: Erro em UserPermissionsView.get: {e}")
            return Response(
                {"detail": f"Erro ao buscar permissões: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    post=extend_schema(
        tags=["Mobile - User"],
        request=AssignUserRoleRequestSerializer,
        responses={
            200: AssignUserRoleResponseSerializer,
            400: DetailSerializer,
            403: DetailSerializer,
            404: DetailSerializer,
            500: DetailSerializer,
        },
    ),
)
class AssignUserRoleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Atribui um papel a um usuário (apenas system_admin pode fazer isso)"""
        try:
            # Verificar se o usuário atual tem permissão
            if not request.user.has_perm("auth.can_manage_permissions"):
                return Response(
                    {
                        "detail": (
                            "Sem permissão para gerenciar papéis de usuários"
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            user_id = request.data.get("user_id")
            role = request.data.get("role")

            if not user_id or not role:
                return Response(
                    {
                        "detail": (
                            "user_id e role são obrigatórios"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if role not in ["system_admin", "office_admin", "regular_user"]:
                return Response(
                    {"detail": "Papel inválido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Buscar o usuário
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Usuário não encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Atribuir o papel
            success = Profile.assign_role(target_user, role)

            if success:
                return Response(
                    {
                        "detail": (
                            f"Papel {role} atribuído com sucesso ao usuário "
                            f"{target_user.username}"
                        ),
                        "user": target_user.username,
                        "role": role,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "Erro ao atribuir papel"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            print(f"DEBUG MOBILE: Erro em AssignUserRoleView.post: {e}")
            return Response(
                {"detail": f"Erro ao atribuir papel: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="Upload de imagem de perfil",
    description="Faz upload de uma nova imagem de perfil para mobile. A imagem será redimensionada automaticamente.",
    tags=["Mobile - User"],
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
        200: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string'},
                'profile_image_url': {'type': 'string'},
                'user': {'type': 'object'}
            }
        },
        400: DetailSerializer,
        401: DetailSerializer
    }
)
@extend_schema(
    summary="Upload de imagem de perfil",
    description="Faz upload de uma nova imagem de perfil para mobile",
    tags=["Mobile - User"],
    methods=['POST'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string'},
                'profile_image_url': {'type': 'string'},
                'user': {'type': 'object'}
            }
        },
        400: DetailSerializer
    }
)
@extend_schema(
    summary="Remover imagem de perfil",
    description="Remove a imagem de perfil atual do usuário mobile",
    tags=["Mobile - User"],
    methods=['DELETE'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string'},
                'user': {'type': 'object'}
            }
        },
        404: DetailSerializer
    }
)
@api_view(['POST', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def manage_profile_image(request):
    """
    Gerencia upload e remoção da imagem de perfil para mobile
    """
    if request.method == 'POST':
        # Upload da imagem
        from .serializers import MobileProfileImageUploadSerializer, MobileUserWithImageSerializer
        
        serializer = MobileProfileImageUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Salva a imagem e atualiza o profile
                profile = serializer.save(user=request.user)
                
                # Retorna dados atualizados do usuário
                user_serializer = MobileUserWithImageSerializer(request.user)
                
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
        from .serializers import MobileUserWithImageSerializer
        
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
                user_serializer = MobileUserWithImageSerializer(request.user)
                
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
    summary="Obter URL da imagem de perfil",
    description="Retorna a URL presigned da imagem de perfil do S3 para mobile (válida por 1 hora)",
    tags=["Mobile - User"],
    responses={
        200: inline_serializer(
            name="MobileProfileImageURLResponse",
            fields={
                "profile_image_url": serializers.URLField(),
                "expires_in": serializers.IntegerField(),
            },
        ),
        404: DetailSerializer
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def serve_profile_image(request, user_id):
    """Retorna URL presigned da imagem de perfil para mobile"""
    try:
        from users.services import S3ImageService
        
        # Buscar profile do usuário
        profile = Profile.objects.get(user_id=user_id)
        
        if not profile.profile_image:
            return Response(
                {"detail": "Usuário não possui imagem de perfil"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Gerar URL presigned
        s3_service = S3ImageService()
        
        try:
            presigned_url = s3_service.generate_presigned_url(profile.profile_image)
            
            return Response(
                {
                    "profile_image_url": presigned_url,
                    "expires_in": 3600  # 1 hora em segundos
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar URL da imagem: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Profile.DoesNotExist:
        return Response(
            {"detail": "Usuário não encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    summary="Renovar token JWT",
    description="Renova o token de acesso usando o refresh token para aplicação mobile",
    tags=["Mobile - User"],
    responses={200: {"type": "object", "properties": {"access": {"type": "string"}}}}
)
class MobileTokenRefreshView(TokenRefreshView):
    """View customizada para refresh token com documentação adequada"""
    pass


# ============================================
# Views para gerenciamento de relacionamentos usuário-paciente
# ============================================

@extend_schema(
    summary="Listar meus pacientes",
    description="Lista todos os pacientes atendidos pelo usuário autenticado",
    tags=["Mobile - User"],
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'relationId': {'type': 'string', 'format': 'uuid'},
                    'patientId': {'type': 'string', 'format': 'uuid'},
                    'patientName': {'type': 'string'},
                    'patientCpf': {'type': 'string'},
                    'patientPhone': {'type': 'string'},
                    'startDate': {'type': 'string', 'format': 'date-time'},
                    'isActive': {'type': 'boolean'}
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
    summary="Adicionar paciente existente aos meus cuidados",
    description="Adiciona um paciente à lista de pacientes atendidos pelo usuário",
    tags=["Mobile - User"],
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
                        "patientName": {"type": "string"},
                        "startDate": {"type": "string", "format": "date-time"}
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
                'patientName': relation.patient.full_name,
                'startDate': relation.start_date
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Remover paciente dos meus cuidados",
    description="Remove um paciente da lista de pacientes atendidos (soft delete)",
    tags=["Mobile - User"],
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
    tags=["Mobile - User"],
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'relationId': {'type': 'string', 'format': 'uuid'},
                    'userId': {'type': 'integer'},
                    'userName': {'type': 'string'},
                    'userEmail': {'type': 'string'},
                    'startDate': {'type': 'string', 'format': 'date-time'},
                    'isActive': {'type': 'boolean'}
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
