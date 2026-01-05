from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, extend_schema_view

from groups.models import Group, Clinic, DeviceClinic, GroupAdmin, UserClinic
from devices.models import Device
from .serializers import (
    MobileGroupSerializer, MobileClinicSerializer, MobileDeviceSerializer,
    MobileGroupWithClinicsSerializer, MobileClinicWithDevicesSerializer,
    MobileDetailResponseSerializer, MobileGroupCreateSerializer
)


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Listar todos os grupos",
        description="Retorna lista simplificada de todos os grupos para mobile",
        responses={200: MobileGroupSerializer(many=True)}
    )
)
class GroupListView(generics.ListAPIView):
    """Lista todos os grupos para mobile"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = MobileGroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    tags=["Mobile - Groups"],
    summary="Criar novo grupo",
    description="Cria um novo grupo e automaticamente torna o usuário logado administrador do grupo",
    methods=['POST'],
    request=MobileGroupCreateSerializer,
    responses={201: MobileGroupSerializer}
)
class GroupCreateView(generics.CreateAPIView):
    """Cria um novo grupo para mobile"""
    serializer_class = MobileGroupCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Salva o grupo com o usuário atual como contexto"""
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override para retornar o grupo criado com o serializer mobile"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        
        # Retornar com o serializer mobile do grupo
        response_serializer = MobileGroupSerializer(group)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Obter grupo com suas clínicas",
        description="Retorna um grupo específico com todas suas clínicas para mobile",
        responses={
            200: MobileGroupWithClinicsSerializer,
            404: MobileDetailResponseSerializer
        }
    )
)
class GroupDetailView(generics.RetrieveAPIView):
    """Detalhe de um grupo com suas clínicas para mobile"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = MobileGroupWithClinicsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Listar clínicas de um grupo",
        description="Retorna todas as clínicas ativas de um grupo específico para mobile",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "group": {"type": "object"},
                    "clinic_count": {"type": "integer"},
                    "clinics": {"type": "array", "items": {"$ref": "#/components/schemas/MobileClinic"}}
                }
            },
            404: MobileDetailResponseSerializer
        }
    )
)
class GroupClinicsView(APIView):
    """Lista todas as clínicas de um grupo específico para mobile"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id, is_active=True)
        except Group.DoesNotExist:
            return Response(
                {"detail": "Grupo não encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        clinics = group.clinics.filter(is_active=True)
        serializer = MobileClinicSerializer(clinics, many=True)
        
        return Response({
            "group": {
                "id": group.id,
                "name": group.name,
                "description": group.description
            },
            "clinic_count": clinics.count(),
            "clinics": serializer.data
        })


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Listar devices de uma clínica",
        description="Retorna todos os devices ativos de uma clínica específica para mobile",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "clinic": {"type": "object"},
                    "device_count": {"type": "integer"},
                    "devices": {"type": "array", "items": {"$ref": "#/components/schemas/MobileDevice"}}
                }
            },
            404: MobileDetailResponseSerializer
        }
    )
)
class ClinicDevicesView(APIView):
    """Lista todos os devices de uma clínica específica para mobile"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, clinic_id):
        try:
            clinic = Clinic.objects.get(id=clinic_id, is_active=True)
        except Clinic.DoesNotExist:
            return Response(
                {"detail": "Clínica não encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Buscar devices ativos da clínica
        device_clinics = clinic.clinic_devices.filter(is_active=True).select_related('device')
        devices = [dc.device for dc in device_clinics]
        device_serializer = MobileDeviceSerializer(devices, many=True)
        
        return Response({
            "clinic": {
                "id": clinic.id,
                "name": clinic.name,
                "group_name": clinic.group.name,
                "group_id": clinic.group.id
            },
            "device_count": len(devices),
            "devices": device_serializer.data
        })


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Listar todos os devices de um grupo",
        description="Retorna todos os devices de todas as clínicas de um grupo específico para mobile",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "group": {"type": "object"},
                    "total_devices": {"type": "integer"},
                    "clinic_count": {"type": "integer"},
                    "devices": {"type": "array", "items": {"$ref": "#/components/schemas/MobileDevice"}}
                }
            },
            404: MobileDetailResponseSerializer
        }
    )
)
class GroupDevicesView(APIView):
    """Lista todos os devices de todas as clínicas de um grupo para mobile"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id, is_active=True)
        except Group.DoesNotExist:
            return Response(
                {"detail": "Grupo não encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Buscar todos os devices das clínicas do grupo
        device_clinics = DeviceClinic.objects.filter(
            clinic__group=group,
            clinic__is_active=True,
            is_active=True
        ).select_related('device', 'clinic')
        
        devices_data = []
        for dc in device_clinics:
            device_data = MobileDeviceSerializer(dc.device).data
            device_data['clinic_info'] = {
                'id': dc.clinic.id,
                'name': dc.clinic.name,
                'assigned_at': dc.assigned_at
            }
            devices_data.append(device_data)
        
        return Response({
            "group": {
                "id": group.id,
                "name": group.name,
                "description": group.description
            },
            "total_devices": len(devices_data),
            "clinic_count": group.clinics.filter(is_active=True).count(),
            "devices": devices_data
        })


@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Obter clínica com seus devices",
        description="Retorna uma clínica específica com todos seus devices para mobile",
        responses={
            200: MobileClinicWithDevicesSerializer,
            404: MobileDetailResponseSerializer
        }
    )
)
@extend_schema_view(
    get=extend_schema(
        tags=["Mobile - Groups"],
        summary="Detalhe de uma clínica",
        description="Retorna os detalhes de uma clínica com seus devices"
    ),
    put=extend_schema(
        tags=["Mobile - Groups"],
        summary="Atualizar clínica",
        description="Atualiza uma clínica existente. Apenas Group Admins do grupo podem atualizar.",
        responses={
            200: MobileClinicSerializer,
            403: MobileDetailResponseSerializer,
            404: MobileDetailResponseSerializer
        }
    ),
    patch=extend_schema(
        tags=["Mobile - Groups"],
        summary="Atualizar clínica parcialmente",
        description="Atualiza parcialmente uma clínica. Apenas Group Admins do grupo podem atualizar.",
        responses={
            200: MobileClinicSerializer,
            403: MobileDetailResponseSerializer,
            404: MobileDetailResponseSerializer
        }
    ),
    delete=extend_schema(
        tags=["Mobile - Groups"],
        summary="Deletar clínica (soft delete)",
        description="Desativa uma clínica. Apenas Group Admins do grupo podem deletar.",
        responses={
            204: None,
            403: MobileDetailResponseSerializer,
            404: MobileDetailResponseSerializer
        }
    )
)
class ClinicDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Gerencia operações GET/PUT/PATCH/DELETE de uma clínica"""
    queryset = Clinic.objects.filter(is_active=True)
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MobileClinicWithDevicesSerializer
        return MobileClinicSerializer
    
    def perform_update(self, serializer):
        clinic = self.get_object()
        user = self.request.user
        
        # Verificar se o usuário é system_admin
        if user.groups.filter(name='system_admin').exists():
            serializer.save()
            return
        
        # Verificar se o usuário é group_admin deste grupo
        is_group_admin = GroupAdmin.objects.filter(
            user=user,
            group=clinic.group,
            is_active=True
        ).exists()
        
        if not is_group_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para atualizar clínicas neste grupo. "
                "Apenas Group Admins do grupo podem atualizar clínicas."
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Verificar se o usuário é system_admin
        if user.groups.filter(name='system_admin').exists():
            instance.is_active = False
            instance.save()
            return
        
        # Verificar se o usuário é group_admin deste grupo
        is_group_admin = GroupAdmin.objects.filter(
            user=user,
            group=instance.group,
            is_active=True
        ).exists()
        
        if not is_group_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para deletar clínicas neste grupo. "
                "Apenas Group Admins do grupo podem deletar clínicas."
            )
        
        # Soft delete
        instance.is_active = False
        instance.save()


@extend_schema_view(
    post=extend_schema(
        tags=["Mobile - Groups"],
        summary="Criar nova clínica",
        description="Cria uma nova clínica em um grupo. Apenas Group Admins do grupo podem criar clínicas.",
        responses={
            201: MobileClinicSerializer,
            403: MobileDetailResponseSerializer
        }
    )
)
class ClinicCreateView(generics.CreateAPIView):
    """Criar uma nova clínica (apenas para Group Admins do grupo)"""
    serializer_class = MobileClinicSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        group_id = serializer.validated_data.get('group').id
        user = self.request.user
        
        # Verificar se o usuário é system_admin
        if user.groups.filter(name='system_admin').exists():
            serializer.save()
            return
        
        # Verificar se o usuário é group_admin deste grupo específico
        is_group_admin = GroupAdmin.objects.filter(
            user=user,
            group_id=group_id,
            is_active=True
        ).exists()
        
        if not is_group_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para criar clínicas neste grupo. "
                "Apenas Group Admins do grupo podem criar clínicas."
            )
        
        serializer.save()


# ============================================================================
# USER-CLINIC ENDPOINTS
# ============================================================================

@extend_schema_view(
    post=extend_schema(
        tags=["Mobile - Groups"],
        summary="Vincular usuário a clínica",
        description="Cria vínculo entre usuário e clínica. Apenas Group Admins e System Admins.",
        responses={
            201: None,
            403: MobileDetailResponseSerializer
        }
    )
)
class UserClinicCreateView(generics.CreateAPIView):
    """Criar vínculo usuário-clínica (apenas para Group Admins)"""
    from groups.api.web.v0.user_clinic_serializers import UserClinicCreateSerializer
    serializer_class = UserClinicCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        clinic = serializer.validated_data.get('clinic')
        user = self.request.user
        
        # Verificar se é system_admin
        if user.groups.filter(name='system_admin').exists():
            serializer.save()
            return
        
        # Verificar se é group_admin do grupo da clínica
        is_group_admin = GroupAdmin.objects.filter(
            user=user,
            group=clinic.group,
            is_active=True
        ).exists()
        
        if not is_group_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para vincular usuários a esta clínica. "
                "Apenas Group Admins do grupo podem fazer isso."
            )
        
        serializer.save()


@extend_schema_view(
    delete=extend_schema(
        tags=["Mobile - Groups"],
        summary="Desvincular usuário de clínica",
        description="Remove vínculo entre usuário e clínica (soft delete). Apenas Group Admins e System Admins.",
        responses={
            204: None,
            403: MobileDetailResponseSerializer,
            404: MobileDetailResponseSerializer
        }
    )
)
class UserClinicDeleteView(generics.DestroyAPIView):
    """Deletar vínculo usuário-clínica (apenas para Group Admins)"""
    queryset = UserClinic.objects.filter(is_active=True)
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Verificar se é system_admin
        if user.groups.filter(name='system_admin').exists():
            from django.utils import timezone
            instance.is_active = False
            instance.end_date = timezone.now()
            instance.save()
            return
        
        # Verificar se é group_admin do grupo da clínica
        is_group_admin = GroupAdmin.objects.filter(
            user=user,
            group=instance.clinic.group,
            is_active=True
        ).exists()
        
        if not is_group_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Você não tem permissão para desvincular usuários desta clínica. "
                "Apenas Group Admins do grupo podem fazer isso."
            )
        
        # Soft delete
        from django.utils import timezone
        instance.is_active = False
        instance.end_date = timezone.now()
        instance.save()


