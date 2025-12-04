from rest_framework import permissions, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from django.contrib.auth import get_user_model

# DRF Spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import ProfileImageUploadSerializer, UserWithImageSerializer
from users.models import Profile

User = get_user_model()

@extend_schema(
    operation_id="upload_profile_image",
    summary="Upload de imagem de perfil",
    description="Faz upload de uma imagem de perfil para o S3 e atualiza o usuário. A imagem será redimensionada automaticamente para 800x800px mantendo proporção.",
    tags=["User Management"],
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
                'detail': {'type': 'string', 'example': 'Imagem de perfil atualizada com sucesso'},
                'image_url': {'type': 'string', 'example': 'https://bucket.s3.region.amazonaws.com/profiles/user_1/avatar.jpg'},
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
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([parsers.MultiPartParser, parsers.FormParser])
def upload_profile_image(request):
    """
    Endpoint para upload de imagem de perfil do usuário autenticado
    """
    serializer = ProfileImageUploadSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Salva a imagem e atualiza o profile
            profile = serializer.save(user=request.user)
            
            # Retorna dados atualizados do usuário
            user_serializer = UserWithImageSerializer(request.user)
            
            return Response({
                'detail': 'Imagem de perfil atualizada com sucesso',
                'image_url': profile.get_profile_image_url(),
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'detail': f'Erro interno ao processar imagem: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    operation_id="delete_profile_image",
    summary="Remove imagem de perfil",
    description="Remove a imagem de perfil atual do usuário, deletando do S3 e limpando o campo no banco.",
    tags=["User Management"],
    request=None,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Imagem de perfil removida com sucesso'},
                'user': UserWithImageSerializer
            }
        },
        404: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Usuário não possui imagem de perfil'}
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
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_image(request):
    """
    Remove a imagem de perfil do usuário autenticado
    """
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
    operation_id="get_user_profile",
    summary="Obter perfil do usuário",
    description="Retorna dados completos do perfil do usuário autenticado, incluindo URL da imagem de perfil.",
    tags=["User Management"],
    request=None,
    responses={
        200: UserWithImageSerializer,
        401: {
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'Token de autenticação necessário'}
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_profile(request):
    """
    Retorna dados completos do usuário autenticado incluindo imagem de perfil
    """
    user_serializer = UserWithImageSerializer(request.user)
    return Response(user_serializer.data, status=status.HTTP_200_OK)

