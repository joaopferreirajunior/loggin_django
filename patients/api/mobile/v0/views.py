# patients/api/mobile/v0/views.py

from rest_framework import status, permissions, parsers, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer
from django.shortcuts import get_object_or_404
from patients.models import Patient, MedicalRecord
from .serializers import (
    PatientSerializer, MedicalRecordSerializer, DetailSerializer,
    PatientPhotoUploadSerializer, PatientWithPhotoSerializer
)


@extend_schema(
    summary="Listar pacientes",
    description="Retorna lista paginada de pacientes do grupo do usuário logado para aplicação mobile",
    tags=["Mobile - Patients"],
    methods=['GET'],
    responses={200: PatientSerializer(many=True)}
)
@extend_schema(
    summary="Criar paciente",
    description="Cria um novo paciente na aplicação mobile",
    tags=["Mobile - Patients"],
    methods=['POST'],
    request=PatientSerializer,
    responses={
        201: PatientSerializer,
        400: DetailSerializer
    }
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def manage_patients_list(request):
    """Lista pacientes (GET) ou cria novo paciente (POST)"""
    
    if request.method == 'GET':
        # Listar pacientes
        user = request.user
        
        # System admin pode ver todos
        if user.groups.filter(name='system_admin').exists():
            patients = Patient.objects.filter(is_active=True).order_by('-created_at')
        else:
            # Buscar grupos do usuário via UserClinic ou GroupAdmin
            from groups.models import UserClinic, GroupAdmin
            
            user_groups = []
            
            # Grupos via clínicas
            user_clinics = UserClinic.objects.filter(
                user=user,
                is_active=True
            ).select_related('clinic__group').values_list('clinic__group_id', flat=True)
            user_groups.extend(user_clinics)
            
            # Grupos via admin
            admin_groups = GroupAdmin.objects.filter(
                user=user,
                is_active=True
            ).values_list('group_id', flat=True)
            user_groups.extend(admin_groups)
            
            if not user_groups:
                return Response([], status=status.HTTP_200_OK)
            
            # Filtrar pacientes dos grupos do usuário
            patients = Patient.objects.filter(
                is_active=True,
                group_id__in=user_groups
            ).order_by('-created_at')
        
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Criar paciente
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Verificar se é system_admin (pode criar em qualquer grupo)
            if user.groups.filter(name='system_admin').exists():
                patient = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            # Para usuários não-admin, associar automaticamente ao grupo do usuário
            from groups.models import UserClinic, GroupAdmin
            
            # Buscar clínica do usuário (primeira clínica ativa)
            user_clinic = UserClinic.objects.filter(
                user=user,
                is_active=True
            ).select_related('clinic', 'clinic__group').first()
            
            if user_clinic:
                # Usuário está vinculado a uma clínica -> associar ao grupo da clínica
                patient = serializer.save(group=user_clinic.clinic.group)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            # Se não está vinculado a clínica, verificar se é admin de algum grupo
            group_admin = GroupAdmin.objects.filter(
                user=user,
                is_active=True
            ).select_related('group').first()
            
            if group_admin:
                # Usuário é admin de um grupo -> associar ao grupo
                patient = serializer.save(group=group_admin.group)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            # Não está vinculado a nenhuma clínica nem é admin de grupo
            return Response(
                {"detail": "Você não está vinculado a nenhuma clínica ou grupo. Apenas usuários vinculados podem criar pacientes."},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Obter paciente",
    description="Retorna dados de um paciente específico do mesmo grupo",
    tags=["Mobile - Patients"],
    methods=['GET'],
    responses={
        200: PatientSerializer,
        404: DetailSerializer,
        403: DetailSerializer
    }
)
@extend_schema(
    summary="Atualizar paciente",
    description="Atualiza dados de um paciente específico",
    tags=["Mobile - Patients"],
    methods=['PUT', 'PATCH'],
    request=PatientSerializer,
    responses={
        200: PatientSerializer,
        400: DetailSerializer,
        404: DetailSerializer,
        403: DetailSerializer
    }
)
@extend_schema(
    summary="Deletar paciente",
    description="Remove um paciente (soft delete)",
    tags=["Mobile - Patients"],
    methods=['DELETE'],
    responses={
        200: DetailSerializer,
        404: DetailSerializer,
        403: DetailSerializer
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def manage_patient_detail(request, patient_id):
    """Gerencia operações de um paciente específico (GET/PUT/PATCH/DELETE)"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    user = request.user
    
    # Verificar permissões (system_admin ou mesmo grupo)
    if not user.groups.filter(name='system_admin').exists():
        from groups.models import UserClinic, GroupAdmin
        
        user_in_patient_group = (
            UserClinic.objects.filter(
                user=user,
                clinic__group=patient.group,
                is_active=True
            ).exists() or
            GroupAdmin.objects.filter(
                user=user,
                group=patient.group,
                is_active=True
            ).exists()
        )
        
        if not user_in_patient_group:
            action = "visualizar" if request.method == 'GET' else "modificar"
            return Response(
                {"detail": f"Você não tem permissão para {action} este paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    if request.method == 'GET':
        # Obter paciente
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Atualizar paciente
        serializer = PatientSerializer(patient, data=request.data, partial=(request.method == 'PATCH'))
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Deletar paciente (soft delete)
        patient.is_active = False
        patient.save()
        return Response(
            {"detail": "Paciente removido com sucesso"},
            status=status.HTTP_200_OK
        )


@extend_schema(
    summary="Listar prontuários",
    description="Retorna todos os prontuários de um paciente",
    tags=["Mobile - Patients"],
    responses={
        200: MedicalRecordSerializer(many=True),
        403: DetailSerializer
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_medical_records(request, patient_id):
    """Lista todos os prontuários de um paciente"""
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    user = request.user
    
    # Verificar se é system_admin
    if not user.groups.filter(name='system_admin').exists():
        from groups.models import UserClinic, GroupAdmin
        
        # Verificar se usuário pertence ao mesmo grupo do paciente
        user_in_patient_group = (
            UserClinic.objects.filter(
                user=user,
                clinic__group=patient.group,
                is_active=True
            ).exists() or
            GroupAdmin.objects.filter(
                user=user,
                group=patient.group,
                is_active=True
            ).exists()
        )
        
        if not user_in_patient_group:
            return Response(
                {"detail": "Você não tem permissão para visualizar prontuários deste paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    records = patient.medical_records.order_by('-created_at')
    serializer = MedicalRecordSerializer(records, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Criar prontuário",
    description="Cria um novo prontuário médico",
    tags=["Mobile - Patients"],
    request=MedicalRecordSerializer,
    responses={
        201: MedicalRecordSerializer,
        400: DetailSerializer,
        403: DetailSerializer
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_medical_record(request):
    """Cria um novo prontuário médico"""
    serializer = MedicalRecordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        patient_id = serializer.validated_data.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id, is_active=True)
        
        # Verificar se é system_admin
        if not user.groups.filter(name='system_admin').exists():
            from groups.models import UserClinic, GroupAdmin
            
            # Verificar se usuário pertence ao mesmo grupo do paciente
            user_in_patient_group = (
                UserClinic.objects.filter(
                    user=user,
                    clinic__group=patient.group,
                    is_active=True
                ).exists() or
                GroupAdmin.objects.filter(
                    user=user,
                    group=patient.group,
                    is_active=True
                ).exists()
            )
            
            if not user_in_patient_group:
                return Response(
                    {"detail": "Você não tem permissão para criar prontuário para este paciente."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        record = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Atualizar prontuário",
    description="Atualiza um prontuário médico específico",
    tags=["Mobile - Patients"],
    request=MedicalRecordSerializer,
    responses={
        200: MedicalRecordSerializer,
        400: DetailSerializer,
        404: DetailSerializer,
        403: DetailSerializer
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_medical_record(request, record_id):
    """Atualiza um prontuário médico"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    user = request.user
    patient = record.patient
    
    # Verificar se é system_admin
    if not user.groups.filter(name='system_admin').exists():
        from groups.models import UserClinic, GroupAdmin
        
        # Verificar se usuário pertence ao mesmo grupo do paciente
        user_in_patient_group = (
            UserClinic.objects.filter(
                user=user,
                clinic__group=patient.group,
                is_active=True
            ).exists() or
            GroupAdmin.objects.filter(
                user=user,
                group=patient.group,
                is_active=True
            ).exists()
        )
        
        if not user_in_patient_group:
            return Response(
                {"detail": "Você não tem permissão para atualizar este prontuário."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = MedicalRecordSerializer(record, data=request.data, partial=(request.method == 'PATCH'))
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# Views para gerenciamento de foto do paciente
# ============================================

@extend_schema(
    summary="Upload de foto do paciente",
    description="Faz upload de uma nova foto do paciente para aplicação mobile",
    tags=["Mobile - Patients"],
    methods=['POST'],
    request=PatientPhotoUploadSerializer,
    responses={
        200: inline_serializer(
            name="MobileUploadPatientPhotoResponse",
            fields={
                "detail": serializers.CharField(),
                "photo_url": serializers.URLField(allow_null=True, required=False),
                "patient": PatientWithPhotoSerializer(),
            },
        ),
        400: DetailSerializer,
        403: DetailSerializer,
        404: DetailSerializer
    }
)
@extend_schema(
    summary="Remover foto do paciente",
    description="Remove a foto do paciente",
    tags=["Mobile - Patients"],
    methods=['DELETE'],
    responses={
        200: inline_serializer(
            name="MobileDeletePatientPhotoResponse",
            fields={
                "detail": serializers.CharField(),
                "patient": PatientWithPhotoSerializer(),
            },
        ),
        403: DetailSerializer,
        404: DetailSerializer
    }
)
@extend_schema(
    summary="Obter URL da foto do paciente",
    description="Retorna a URL presigned da foto do paciente",
    tags=["Mobile - Patients"],
    methods=['GET'],
    responses={
        200: inline_serializer(
            name="MobilePatientPhotoURLResponse",
            fields={
                "photo_url": serializers.URLField(),
                "expires_in": serializers.IntegerField(),
            },
        ),
        403: DetailSerializer,
        404: DetailSerializer
    }
)
@api_view(['POST', 'DELETE', 'GET'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([parsers.MultiPartParser, parsers.FormParser])
def manage_patient_photo(request, patient_id):
    """
    Gerencia upload, remoção e obtenção de URL da foto do paciente
    """
    patient = get_object_or_404(Patient, id=patient_id, is_active=True)
    user = request.user
    
    # Verificar permissão
    if not user.groups.filter(name='system_admin').exists():
        from groups.models import UserClinic, GroupAdmin
        
        user_in_patient_group = (
            UserClinic.objects.filter(
                user=user,
                clinic__group=patient.group,
                is_active=True
            ).exists() or
            GroupAdmin.objects.filter(
                user=user,
                group=patient.group,
                is_active=True
            ).exists()
        )
        
        if not user_in_patient_group:
            return Response(
                {"detail": "Você não tem permissão para acessar a foto deste paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    if request.method == 'POST':
        # Upload de foto
        serializer = PatientPhotoUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                patient = serializer.save(patient=patient)
                patient_serializer = PatientWithPhotoSerializer(patient)
                
                return Response({
                    'detail': 'Foto do paciente atualizada com sucesso',
                    'photo_url': patient.get_patient_photo_url(),
                    'patient': patient_serializer.data
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'detail': f'Erro interno ao processar foto: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Remoção de foto
        if not patient.photo:
            return Response({
                'detail': 'Paciente não possui foto'
            }, status=status.HTTP_404_NOT_FOUND)
        
        success = patient.delete_patient_photo()
        
        if success:
            patient_serializer = PatientWithPhotoSerializer(patient)
            
            return Response({
                'detail': 'Foto do paciente removida com sucesso',
                'patient': patient_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'detail': 'Erro ao remover foto do S3'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'GET':
        # Obter URL da foto
        if not patient.photo:
            return Response(
                {"detail": "Paciente não possui foto"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            photo_url = patient.get_patient_photo_url()
            
            return Response(
                {
                    "photo_url": photo_url,
                    "expires_in": 3600
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar URL da foto: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )