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

    # medicalRecord: o Dart espera UM objeto ou null -> vamos devolver o mais recente
    medicalRecord = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "groupId",
            "fullName",
            "photo",
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

    @extend_schema_field(MedicalRecordSerializer(allow_null=True))
    def get_medicalRecord(self, obj: Patient) -> Optional[Dict[str, Any]]:
        record = obj.medical_records.order_by("-created_at").first()
        if not record:
            return None
        return MedicalRecordSerializer(record).data


@extend_schema_serializer(component_name="WebDetailResponse")
class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()