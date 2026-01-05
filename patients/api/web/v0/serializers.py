# patients/api/web/v0/serializers.py

from rest_framework import serializers
from patients.models import Patient, MedicalRecord, Anamnesis
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from typing import Optional, Dict, Any


@extend_schema_serializer(component_name="WebMedicalRecord")
class MedicalRecordSerializer(serializers.ModelSerializer):
    # patientId no JSON -> patient_id no model (FK)
    patientId = serializers.UUIDField(source="patient_id")
    userId = serializers.IntegerField(source="user_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    clinicalNotes = serializers.CharField(source="clinical_notes")

    class Meta:
        model = MedicalRecord
        fields = (
            "id",
            "patientId",
            "userId",
            "createdAt",
            "complaint",
            "clinicalNotes",
        )
        read_only_fields = ('userId', 'createdAt')


@extend_schema_serializer(component_name="WebAnamnesis")
class AnamnesisSerializer(serializers.ModelSerializer):
    """Serializer para Anamnesis na API Web"""
    userId = serializers.IntegerField(source="user_id", read_only=True)
    patientIds = serializers.ListField(
        child=serializers.UUIDField(),
        source="patients",
        write_only=True,
        required=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    modifiedAt = serializers.DateTimeField(source="modified_at", read_only=True)

    class Meta:
        model = Anamnesis
        fields = (
            "id",
            "userId",
            "patientIds",
            "metadata",
            "createdAt",
            "modifiedAt",
        )
        read_only_fields = ('userId', 'createdAt', 'modifiedAt')

    def create(self, validated_data):
        patient_ids = validated_data.pop('patients')
        anamnesis = Anamnesis.objects.create(**validated_data)
        anamnesis.patients.set(Patient.objects.filter(id__in=patient_ids))
        return anamnesis

    def update(self, instance, validated_data):
        # patient_ids não podem ser modificados
        validated_data.pop('patients', None)
        instance.metadata = validated_data.get('metadata', instance.metadata)
        instance.save()
        return instance


@extend_schema_serializer(component_name="WebAnamnesisDetail")
class AnamnesisDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para Anamnesis incluindo lista de pacientes"""
    userId = serializers.IntegerField(source="user_id", read_only=True)
    patients = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    modifiedAt = serializers.DateTimeField(source="modified_at", read_only=True)

    class Meta:
        model = Anamnesis
        fields = (
            "id",
            "userId",
            "patients",
            "metadata",
            "createdAt",
            "modifiedAt",
        )

    def get_patients(self, obj):
        return [{"id": p.id, "fullName": p.full_name} for p in obj.patients.all()]


@extend_schema_serializer(component_name="WebPatient")
class PatientSerializer(serializers.ModelSerializer):
    groupId = serializers.UUIDField(source="group_id", read_only=True)
    fullName = serializers.CharField(source="full_name")
    birthDate = serializers.DateField(source="birth_date")
    fullAddress = serializers.CharField(source="full_address", allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    isActive = serializers.BooleanField(source="is_active", default=True, required=False)
    # photo, cpf, phone, email, city, region, cep, gender mapeiam direto
    photo_url = serializers.SerializerMethodField()

    # medicalRecord: o Dart espera UM objeto ou null -> vamos devolver o mais recente
    medicalRecord = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "groupId",
            "fullName",
            "photo_url",
            "birthDate",
            "gender",
            "cpf",
            "phone",
            "email",
            "fullAddress",
            "city",
            "region",
            "cep",
            "createdAt",
            "updatedAt",
            "isActive",
            "medicalRecord",
        )

    def get_photo_url(self, obj: Patient) -> Optional[str]:
        """Retorna URL presigned temporária da foto no S3 (válida por 1 hora)"""
        return obj.get_patient_photo_url()
    
    @extend_schema_field(MedicalRecordSerializer(allow_null=True))
    def get_medicalRecord(self, obj: Patient) -> Optional[Dict[str, Any]]:
        record = obj.medical_records.order_by("-created_at").first()
        if not record:
            return None
        return MedicalRecordSerializer(record).data


@extend_schema_serializer(component_name="WebDetailResponse")
class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


@extend_schema_serializer(component_name="WebPatientPhotoUpload")
class PatientPhotoUploadSerializer(serializers.Serializer):
    """
    Serializer para upload de foto do paciente
    """
    patient_photo = serializers.ImageField(
        required=True,
        help_text="Foto do paciente (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_patient_photo(self, value):
        """
        Valida a imagem usando o serviço S3ImageService
        """
        from users.services import S3ImageService
        s3_service = S3ImageService()
        is_valid, error_message = s3_service.validate_image(value)
        
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value
    
    def save(self, patient):
        """
        Processa e salva a foto no S3
        """
        try:
            from users.services import S3ImageService
            patient_photo = self.validated_data['patient_photo']
            s3_service = S3ImageService()
            
            # Remove foto anterior se existir
            if patient.photo:
                patient.delete_patient_photo()
            
            # Upload nova foto (usando o ID do paciente como prefixo)
            success, message, s3_key = s3_service.process_and_upload_profile_image(
                f"patient_{patient.id}", patient_photo
            )
            
            if not success:
                raise serializers.ValidationError(f"Erro no upload: {message}")
            
            # Atualiza o paciente com o novo path
            patient.photo = s3_key
            patient.save()
            
            return patient
            
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise serializers.ValidationError(f"Erro inesperado ao processar foto: {str(e)}")


@extend_schema_serializer(component_name="WebPatientWithPhoto")
class PatientWithPhotoSerializer(serializers.ModelSerializer):
    """Serializer do paciente com URL da foto"""
    group_id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    birth_date = serializers.DateField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "group_id",
            "full_name",
            "photo_url",
            "birth_date",
            "gender",
            "cpf",
            "phone",
            "email",
            "full_address",
            "city",
            "region",
            "cep",
            "created_at",
            "updated_at",
            "is_active",
        )
    
    def get_photo_url(self, obj):
        return obj.get_patient_photo_url()