from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group, Permission
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserRegisterSerializer, UserSerializer, UserProfileSerializer
from users.models import UserProfile

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def register(request):
    try:
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"DEBUG: Usuário {user.username} criado com sucesso")
            return Response({"detail": "Conta criada com sucesso!"}, status=status.HTTP_201_CREATED)
        else:
            print(f"DEBUG: Erros de validação no registro: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"DEBUG: Erro interno no registro: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"detail": f"Erro interno do servidor: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    username_or_email = request.data.get("username")
    password = request.data.get("password")
    
    print(f"DEBUG: Tentativa de login com: '{username_or_email}'")
    print(f"DEBUG: Request headers: {request.headers}")

    # Primeiro, verifica se é um email válido
    if "@" in username_or_email:
        # É um email, tenta encontrar o usuário por email
        try:
            user_obj = User.objects.get(email=username_or_email)
            username = user_obj.username
            print(f"DEBUG: Email '{username_or_email}' encontrado, username: '{username}'")
        except User.DoesNotExist:
            print(f"DEBUG: Email '{username_or_email}' não encontrado")
            return Response({"detail": "Email não encontrado"}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        # É um username
        username = username_or_email
        print(f"DEBUG: Usando como username: '{username}'")

    user = authenticate(username=username, password=password)
    print(f"DEBUG: Resultado da autenticação: {user}")
    
    if user is not None:
        login(request, user)
        print(f"DEBUG: Login realizado com sucesso para usuário: {user.username}")
        return Response({"detail": "Login bem-sucedido"}, status=status.HTTP_200_OK)
    else:
        print(f"DEBUG: Falha na autenticação para username: '{username}'")
        return Response({"detail": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
@csrf_exempt
def logout_view(request):
    logout(request)
    return Response({"detail": "Logout realizado com sucesso"}, status=status.HTTP_200_OK)


#Retorna os dados completos do próprio usuário logado
class MeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        """
        Atualiza parcialmente os campos do perfil do próprio usuário (cpf, birth, phone).
        Exemplo JSON:
        { "cpf": "123.456.789-10", "phone": "+55 16 99999-0000" }
        """
        try:
            # Garante que o profile existe
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            if created:
                print(f"DEBUG: Profile criado para usuário: {request.user.username}")
                
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"DEBUG: Erro em MeProfileView.patch: {e}")
            return Response({"detail": f"Erro ao atualizar perfil: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Retorna os dados do perfil do próprio usuário logado."""
        try:
            # Garante que o profile existe
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            if created:
                print(f"DEBUG: Profile criado para usuário: {request.user.username}")
            
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"DEBUG: Erro em MeProfileView.get: {e}")
            return Response({"detail": f"Erro ao buscar perfil do usuário: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#Retorna os dados de auth_user do próprio usuário logado
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retorna os dados do próprio usuário logado."""
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            print(f"DEBUG: Erro em MeView.get: {e}")
            return Response({"detail": f"Erro ao buscar dados do usuário: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#View para gerenciar permissões e grupos de usuário
class UserPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Retorna as permissões e grupo do usuário atual"""
        try:
            user = request.user
            profile = user.profile
            
            # Dados do usuário e permissões
            user_data = {
                "user_role": profile.get_user_role(),
                "is_system_admin": profile.is_system_admin(),
                "is_office_admin": profile.is_office_admin(),
                "is_regular_user": profile.is_regular_user(),
                "groups": [group.name for group in user.groups.all()],
                "permissions": list(user.get_all_permissions()),
                "can_manage_users": profile.can_manage_users(),
                "can_view_all_users": profile.can_view_all_users(),
                "can_access_admin": profile.can_access_admin(),
            }
            
            return Response(user_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"DEBUG: Erro em UserPermissionsView.get: {e}")
            return Response({"detail": f"Erro ao buscar permissões: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AssignUserRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Atribui um papel a um usuário (apenas system_admin pode fazer isso)"""
        try:
            # Verificar se o usuário atual tem permissão
            if not request.user.has_perm('auth.can_manage_permissions'):
                return Response({"detail": "Sem permissão para gerenciar papéis de usuários"}, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            role = request.data.get('role')
            
            if not user_id or not role:
                return Response({"detail": "user_id e role são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)
            
            if role not in ['system_admin', 'office_admin', 'regular_user']:
                return Response({"detail": "Papel inválido"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Buscar o usuário
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"detail": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
            # Atribuir o papel
            success = UserProfile.assign_role(target_user, role)
            
            if success:
                return Response({
                    "detail": f"Papel {role} atribuído com sucesso ao usuário {target_user.username}",
                    "user": target_user.username,
                    "role": role
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Erro ao atribuir papel"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"DEBUG: Erro em AssignUserRoleView.post: {e}")
            return Response({"detail": f"Erro ao atribuir papel: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
