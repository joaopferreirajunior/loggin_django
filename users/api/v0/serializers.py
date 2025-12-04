from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Profile
from users.services import S3ImageService

# DRF Spectacular imports
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

User = get_user_model()

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Upload de imagem de perfil",
            description="Arquivo de imagem para upload (JPEG, PNG, WebP até 5MB)",
            value={
                "profile_image": "binary_image_data"
            },
        )
    ]
)
class ProfileImageUploadSerializer(serializers.Serializer):
    """
    Serializer para upload de imagem de perfil
    """
    profile_image = serializers.ImageField(
        required=True,
        help_text="Imagem de perfil (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_profile_image(self, value):
        """
        Valida a imagem usando o serviço S3ImageService
        """
        s3_service = S3ImageService()
        is_valid, error_message = s3_service.validate_image(value)
        
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value
    
    def save(self, user):
        """
        Processa e salva a imagem no S3
        """
        profile_image = self.validated_data['profile_image']
        s3_service = S3ImageService()
        
        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Remove imagem anterior se existir
        if profile.profile_image:
            profile.delete_profile_image()
        
        # Upload nova imagem
        success, message, s3_key = s3_service.process_and_upload_profile_image(
            user.id, profile_image
        )
        
        if not success:
            raise serializers.ValidationError(f"Erro no upload: {message}")
        
        # Atualiza o profile com o novo path
        profile.profile_image = s3_key
        profile.save()
        
        return profile

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Profile com imagem",
            value={
                "id": 1,
                "username": "joao123",
                "email": "joao@email.com",
                "profile": {
                    "cpf": "12345678901",
                    "birth": "1990-01-15", 
                    "phone": "(11) 99999-9999",
                    "profile_image_url": "https://medicalsan-uploads.s3.us-east-1.amazonaws.com/profiles/user_1/avatar_123.jpg"
                }
            }
        )
    ]
)
class UserWithImageSerializer(serializers.ModelSerializer):
    """
    Serializer do usuário incluindo URL da imagem de perfil
    """
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
    
    def get_profile(self, obj):
        """Retorna dados do perfil incluindo URL da imagem"""
        try:
            profile = obj.profile
            profile_data = {
                'cpf': profile.cpf,
                'birth': profile.birth,
                'phone': profile.phone,
                'email_confirmed': profile.email_confirmed,
                'profile_image_url': profile.get_profile_image_url()
            }
            return profile_data
        except Profile.DoesNotExist:
            return {
                'cpf': None,
                'birth': None, 
                'phone': None,
                'email_confirmed': False,
                'profile_image_url': None
            }