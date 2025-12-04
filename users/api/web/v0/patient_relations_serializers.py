# users/api/web/v0/patient_relations_serializers.py

from rest_framework import serializers
from users.models import UserPatientRelation
from drf_spectacular.utils import extend_schema_serializer
from django.contrib.auth import get_user_model

User = get_user_model()


@extend_schema_serializer(component_name="WebUserPatientRelation")
class UserPatientRelationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPatientRelation
        fields = (
            'id', 'user', 'patient', 'user_name', 'patient_name',
            'is_active', 'start_date', 'end_date', 'notes', 'created', 'modified'
        )
        read_only_fields = ('id', 'created', 'modified', 'start_date')
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_patient_name(self, obj):
        return obj.patient.full_name


@extend_schema_serializer(component_name="WebCreateUserPatientRelation")
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


@extend_schema_serializer(component_name="WebUserPatientsListItem")
class UserPatientsListSerializer(serializers.Serializer):
    """Serializer para listar os pacientes de um usuário"""
    relation_id = serializers.UUIDField(source='id')
    patient_id = serializers.UUIDField(source='patient.id')
    patient_name = serializers.CharField(source='patient.full_name')
    patient_cpf = serializers.CharField(source='patient.cpf')
    patient_phone = serializers.CharField(source='patient.phone')
    start_date = serializers.DateTimeField()
    is_active = serializers.BooleanField()


@extend_schema_serializer(component_name="WebPatientDoctorsListItem") 
class PatientDoctorsListSerializer(serializers.Serializer):
    """Serializer para listar os médicos de um paciente"""
    relation_id = serializers.UUIDField(source='id')
    user_id = serializers.IntegerField(source='user.id')
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email')
    start_date = serializers.DateTimeField()
    is_active = serializers.BooleanField()
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username