# patients/api/web/v0/serializers.py

from rest_framework import serializers
from patients.models import Patient, MedicalRecord
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from typing import Optional, Dict, Any


@extend_schema_serializer(component_name="WebMedicalRecord")
class MedicalRecordSerializer(serializers.ModelSerializer):
    # patientId no JSON -> patient_id no model (FK)
    patientId = serializers.UUIDField(source="patient_id")
    createdAt = serializers.DateTimeField(source="created_at")
    doctorName = serializers.CharField(source="doctor_name")
    clinicalNotes = serializers.CharField(source="clinical_notes")

    class Meta:
        model = MedicalRecord
        fields = (
            "id",
            "patientId",
            "createdAt",
            "doctorName",
            "complaint",
            "clinicalNotes",
            "anamnese",  # JSON cru, estrutura igual à que o front manda
        )


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


class PatientWithPhotoSerializer(serializers.ModelSerializer):
    """Serializer do paciente com URL da foto"""
    groupId = serializers.UUIDField(source="group_id", read_only=True)
    fullName = serializers.CharField(source="full_name", read_only=True)
    birthDate = serializers.DateField(source="birth_date", read_only=True)
    fullAddress = serializers.CharField(source="full_address", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    isActive = serializers.BooleanField(source="is_active", read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "groupId",
            "fullName",
            "photo",
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
        )
    
    def get_photo_url(self, obj):
        return obj.get_patient_photo_url()