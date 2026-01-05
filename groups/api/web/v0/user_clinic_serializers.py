from rest_framework import serializers
from groups.models import UserClinic
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_serializer

User = get_user_model()


@extend_schema_serializer(component_name="WebUserClinic")
class UserClinicSerializer(serializers.ModelSerializer):
    """Serializer para listar vínculos usuário-clínica"""
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    clinic_id = serializers.UUIDField(source='clinic.id', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    group_name = serializers.CharField(source='clinic.group.name', read_only=True)
    group_id = serializers.UUIDField(source='clinic.group.id', read_only=True)
    
    class Meta:
        model = UserClinic
        fields = [
            'id', 'user_id', 'username', 'user_email', 'user_full_name',
            'clinic_id', 'clinic_name', 'group_id', 'group_name',
            'role', 'start_date', 'end_date', 'is_active',
            'created', 'modified'
        ]
    
    def get_user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


@extend_schema_serializer(component_name="WebUserClinicCreate")
class UserClinicCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar vínculo usuário-clínica"""
    
    class Meta:
        model = UserClinic
        fields = ['user', 'clinic', 'role']
    
    def validate(self, data):
        """Validar se já existe um vínculo ativo"""
        user = data.get('user')
        clinic = data.get('clinic')
        
        existing = UserClinic.objects.filter(
            user=user,
            clinic=clinic,
            is_active=True
        ).exists()
        
        if existing:
            raise serializers.ValidationError(
                "Este usuário já está vinculado a esta clínica."
            )
        
        return data
