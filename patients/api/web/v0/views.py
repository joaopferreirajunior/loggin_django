# patients/api/web/v0/views.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from patients.models import Patient, MedicalRecord
from .serializers import PatientSerializer, MedicalRecordSerializer, DetailSerializer


@extend_schema(
    summary="Listar pacientes",
    description="Retorna lista paginada de pacientes para aplicação web",
    tags=["Web - Patients"],
    responses={200: PatientSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_patients(request):
    """Lista todos os pacientes ativos"""
    patients = Patient.objects.filter(is_active=True).order_by('-created_at')
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Criar paciente",
    description="Cria um novo paciente na aplicação web",
    tags=["Web - Patients"],
    request=PatientSerializer,
    responses={
        201: PatientSerializer,
        400: DetailSerializer
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_patient(request):
    """Cria um novo paciente"""
    serializer = PatientSerializer(data=request.data)
    if serializer.is_valid():
        clinic_id = serializer.validated_data.get('clinic')
        
        # Se uma clínica foi especificada, validar se o usuário está associado a ela
        if clinic_id:
            from groups.models import UserClinic
            
            # Verificar se é system_admin
            if not request.user.groups.filter(name='system_admin').exists():
                # Verificar se o usuário está vinculado à clínica
                is_user_in_clinic = UserClinic.objects.filter(
                    user=request.user,
                    clinic=clinic_id,
                    is_active=True
                ).exists()
                
                if not is_user_in_clinic:
                    return Response(
                        {"detail": "Você não tem permissão para criar pacientes nesta clínica. Apenas usuários vinculados à clínica podem criar pacientes nela."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        patient = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Obter paciente",
    description="Retorna dados de um paciente específico",
    tags=["Web - Patients"],
    responses={
        200: PatientSerializer,
        404: DetailSerializer
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_patient(request, patient_id):
    """Obtém dados de um paciente específico"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    serializer = PatientSerializer(patient)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Atualizar paciente",
    description="Atualiza dados de um paciente específico",
    tags=["Web - Patients"],
    request=PatientSerializer,
    responses={
        200: PatientSerializer,
        400: DetailSerializer,
        404: DetailSerializer
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_patient(request, patient_id):
    """Atualiza dados de um paciente"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    serializer = PatientSerializer(patient, data=request.data, partial=(request.method == 'PATCH'))
    
    if serializer.is_valid():
        clinic_id = serializer.validated_data.get('clinic')
        
        # Se a clínica está sendo alterada, validar se o usuário está associado à nova clínica
        if clinic_id and clinic_id != patient.clinic:
            from groups.models import UserClinic
            
            # Verificar se é system_admin
            if not request.user.groups.filter(name='system_admin').exists():
                # Verificar se o usuário está vinculado à nova clínica
                is_user_in_clinic = UserClinic.objects.filter(
                    user=request.user,
                    clinic=clinic_id,
                    is_active=True
                ).exists()
                
                if not is_user_in_clinic:
                    return Response(
                        {"detail": "Você não tem permissão para associar pacientes a esta clínica. Apenas usuários vinculados à clínica podem fazê-lo."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Deletar paciente",
    description="Remove um paciente (soft delete)",
    tags=["Web - Patients"],
    responses={
        200: DetailSerializer,
        404: DetailSerializer
    }
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_patient(request, patient_id):
    """Remove um paciente (soft delete)"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    patient.is_active = False
    patient.save()
    return Response({'detail': 'Paciente removido com sucesso'}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Listar prontuários",
    description="Retorna todos os prontuários de um paciente",
    tags=["Web - Patients"],
    responses={200: MedicalRecordSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_medical_records(request, patient_id):
    """Lista todos os prontuários de um paciente"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    records = patient.medical_records.order_by('-created_at')
    serializer = MedicalRecordSerializer(records, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Criar prontuário",
    description="Cria um novo prontuário médico",
    tags=["Web - Patients"],
    request=MedicalRecordSerializer,
    responses={
        201: MedicalRecordSerializer,
        400: DetailSerializer
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_medical_record(request):
    """Cria um novo prontuário médico"""
    serializer = MedicalRecordSerializer(data=request.data)
    if serializer.is_valid():
        record = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Atualizar prontuário",
    description="Atualiza um prontuário médico específico",
    tags=["Web - Patients"],
    request=MedicalRecordSerializer,
    responses={
        200: MedicalRecordSerializer,
        400: DetailSerializer,
        404: DetailSerializer
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_medical_record(request, record_id):
    """Atualiza um prontuário médico"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    serializer = MedicalRecordSerializer(record, data=request.data, partial=(request.method == 'PATCH'))
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)