# users/api/mobile/v0/patient_relations_serializers.py

from rest_framework import serializers
from users.models import UserPatientRelation
from drf_spectacular.utils import extend_schema_serializer
from django.contrib.auth import get_user_model

User = get_user_model()


@extend_schema_serializer(component_name="MobileUserPatientRelation")
class UserPatientRelationSerializer(serializers.ModelSerializer):
    userName = serializers.SerializerMethodField()
    patientName = serializers.SerializerMethodField()
    startDate = serializers.DateTimeField(source='start_date')
    endDate = serializers.DateTimeField(source='end_date')
    isActive = serializers.BooleanField(source='is_active')
    createdAt = serializers.DateTimeField(source='created', read_only=True)
    updatedAt = serializers.DateTimeField(source='modified', read_only=True)
    
    class Meta:
        model = UserPatientRelation
        fields = (
            'id', 'user', 'patient', 'userName', 'patientName',
            'isActive', 'startDate', 'endDate', 'notes', 'createdAt', 'updatedAt'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt', 'startDate')
    
    def get_userName(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_patientName(self, obj):
        return obj.patient.full_name


@extend_schema_serializer(component_name="MobileCreateUserPatientRelation")
class CreateUserPatientRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPatientRelation
        fields = ('patient', 'notes')
    
    def create(self, validated_data):
        # O user é definido na view baseado no usuário autenticado
        user = self.context['request'].user
        relation, created = UserPatientRelation.create_relation(
            user=user,
            patient=validated_data['patient'],
            notes=validated_data.get('notes')
        )
        return relation


@extend_schema_serializer(component_name="MobileUserPatientsListItem")
class UserPatientsListSerializer(serializers.Serializer):
    """Serializer para listar os pacientes de um usuário"""
    relationId = serializers.UUIDField(source='id')
    patientId = serializers.UUIDField(source='patient.id')
    patientName = serializers.CharField(source='patient.full_name')
    patientCpf = serializers.CharField(source='patient.cpf')
    patientPhone = serializers.CharField(source='patient.phone')
    startDate = serializers.DateTimeField(source='start_date')
    isActive = serializers.BooleanField(source='is_active')


@extend_schema_serializer(component_name="MobilePatientDoctorsListItem") 
class PatientDoctorsListSerializer(serializers.Serializer):
    """Serializer para listar os profissionais que atendem um paciente"""
    relationId = serializers.UUIDField(source='id')
    userId = serializers.IntegerField(source='user.id')
    userName = serializers.SerializerMethodField()
    userEmail = serializers.EmailField(source='user.email')
    startDate = serializers.DateTimeField(source='start_date')
    isActive = serializers.BooleanField(source='is_active')
    
    def get_userName(self, obj):
        return obj.user.get_full_name() or obj.user.username