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
        user = request.user
        
        # Verificar se é system_admin (pode criar em qualquer grupo)
        if user.groups.filter(name='system_admin').exists():
            patient = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Para usuários não-admin, associar automaticamente ao grupo do usuário
        from groups.models import UserClinic
        
        # Buscar clínica do usuário (primeira clínica ativa)
        user_clinic = UserClinic.objects.filter(
            user=user,
            is_active=True
        ).select_related('clinic', 'clinic__group').first()
        
        if not user_clinic:
            return Response(
                {"detail": "Você não está vinculado a nenhuma clínica. Apenas usuários vinculados a clínicas podem criar pacientes."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Associar automaticamente ao grupo da clínica do usuário
        patient = serializer.save(group=user_clinic.clinic.group)
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
    user = request.user
    
    # Verificar se é system_admin
    if not user.groups.filter(name='system_admin').exists():
        # Verificar se o usuário pertence ao mesmo grupo do paciente
        from groups.models import UserClinic
        
        user_in_patient_group = UserClinic.objects.filter(
            user=user,
            clinic__group=patient.group,
            is_active=True
        ).exists()
        
        if not user_in_patient_group:
            return Response(
                {"detail": "Você não tem permissão para editar este paciente. Apenas usuários do mesmo grupo podem editar pacientes."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = PatientSerializer(patient, data=request.data, partial=(request.method == 'PATCH'))
    
    if serializer.is_valid():
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