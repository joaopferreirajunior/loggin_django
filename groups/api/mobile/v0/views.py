from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, extend_schema_view

from groups.models import Group, Clinic, DeviceClinic
from devices.models import Device
from .serializers import (
    MobileGroupSerializer, MobileClinicSerializer, MobileDeviceSerializer,
    MobileGroupWithClinicsSerializer, MobileClinicWithDevicesSerializer,
    MobileDetailResponseSerializer
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
class ClinicDetailView(generics.RetrieveAPIView):
    """Detalhe de uma clínica com seus devices para mobile"""
    queryset = Clinic.objects.filter(is_active=True)
    serializer_class = MobileClinicWithDevicesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]