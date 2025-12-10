from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from groups.models import Group, Clinic, DeviceClinic
from devices.models import Device
from .serializers import (
    GroupSerializer, ClinicSerializer, DeviceSerializer,
    GroupWithClinicsSerializer, ClinicWithDevicesSerializer,
    DeviceClinicSerializer
)


@extend_schema_view(
    get=extend_schema(
        tags=["Web - Groups"],
        summary="Listar todos os grupos",
        description="Retorna lista de todos os grupos com informações básicas"
    )
)
class GroupListView(generics.ListAPIView):
    """Lista todos os grupos"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        tags=["Web - Groups"],
        summary="Obter grupo com suas clínicas",
        description="Retorna um grupo específico com todas suas clínicas"
    )
)
class GroupDetailView(generics.RetrieveAPIView):
    """Detalhe de um grupo com suas clínicas"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupWithClinicsSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        tags=["Web - Groups"],
        summary="Listar clínicas de um grupo",
        description="Retorna todas as clínicas ativas de um grupo específico"
    )
)
class GroupClinicsView(APIView):
    """Lista todas as clínicas de um grupo específico"""
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
        serializer = ClinicSerializer(clinics, many=True)
        
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
        tags=["Web - Groups"],
        summary="Listar devices de uma clínica",
        description="Retorna todos os devices ativos de uma clínica específica"
    )
)
class ClinicDevicesView(APIView):
    """Lista todos os devices de uma clínica específica"""
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
        device_serializer = DeviceSerializer(devices, many=True)
        
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
        tags=["Web - Groups"],
        summary="Listar todos os devices de um grupo",
        description="Retorna todos os devices de todas as clínicas de um grupo específico"
    )
)
class GroupDevicesView(APIView):
    """Lista todos os devices de todas as clínicas de um grupo"""
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
            device_data = DeviceSerializer(dc.device).data
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
        tags=["Web - Groups"],
        summary="Obter clínica com seus devices",
        description="Retorna uma clínica específica com todos seus devices"
    )
)
class ClinicDetailView(generics.RetrieveAPIView):
    """Detalhe de uma clínica com seus devices"""
    queryset = Clinic.objects.filter(is_active=True)
    serializer_class = ClinicWithDevicesSerializer
    permission_classes = [permissions.IsAuthenticated]