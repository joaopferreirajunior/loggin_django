from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegisterSerializer

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    try:
        user_obj = User.objects.get(email=username)
        username = user_obj.username
    except User.DoesNotExist:
        pass

    user = authenticate(username=username, password=password)
    if user is not None:
        # 🔑 Gera o token JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            "detail": "Login bem-sucedido",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    else:
        return Response({"detail": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": "success",
            "detail": "Conta criada com sucesso!",
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)
    return Response({
        "status": "error",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logout realizado com sucesso"}, status=status.HTTP_200_OK)
    
