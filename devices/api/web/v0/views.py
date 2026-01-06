from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from devices.models import Device, TelemetryModule, DeviceTelemetryModule
from .serializers import (
    DeviceSerializer, DeviceCreateSerializer, TelemetryModuleSerializer, 
    TelemetryModuleCreateSerializer, DeviceTelemetryModuleSerializer,
    DeviceTelemetryModuleLinkSerializer
)


@extend_schema(
    operation_id="create_device",
    summary="Criar device",
    description="Cria um novo device no sistema",
    request=DeviceCreateSerializer,
    responses={
        201: DeviceSerializer,
        400: OpenApiResponse(description="Dados inválidos")
    },
    tags=["Web - Devices"]
)
class DeviceCreateView(generics.CreateAPIView):
    """Cria um novo device"""
    queryset = Device.objects.all()
    serializer_class = DeviceCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        
        # Retornar o device criado com o serializer de resposta
        response_serializer = DeviceSerializer(device)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="test_device",
    summary="Marcar device como testado",
    description="Marca um device como testado, definindo tested=True e tested_at com timestamp atual",
    responses={
        200: DeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceTestView(APIView):
    """Marca um device como testado"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        
        # Marcar como testado
        device.tested = True
        device.tested_at = timezone.now()
        device.save()
        
        serializer = DeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="sell_device",
    summary="Marcar device como vendido",
    description="Marca um device como vendido, definindo sold=True e sold_at com timestamp atual",
    responses={
        200: DeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceSoldView(APIView):
    """Marca um device como vendido"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        
        # Marcar como vendido
        device.sold = True
        device.sold_at = timezone.now()
        device.save()
        
        serializer = DeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="create_telemetry_module",
    summary="Criar módulo de telemetria",
    description="Cria um novo módulo de telemetria no sistema",
    request=TelemetryModuleCreateSerializer,
    responses={
        201: TelemetryModuleSerializer,
        400: OpenApiResponse(description="Dados inválidos")
    },
    tags=["Web - Devices"]
)
class TelemetryModuleCreateView(generics.CreateAPIView):
    """Cria um novo módulo de telemetria"""
    queryset = TelemetryModule.objects.all()
    serializer_class = TelemetryModuleCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = serializer.save()
        
        # Retornar o módulo criado com o serializer de resposta
        response_serializer = TelemetryModuleSerializer(module)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="link_device_telemetry_module",
    summary="Associar módulo ao device",
    description="Cria uma associação entre um device e um módulo de telemetria",
    request=DeviceTelemetryModuleLinkSerializer,
    responses={
        201: DeviceTelemetryModuleSerializer,
        400: OpenApiResponse(description="Dados inválidos ou associação já existe")
    },
    tags=["Web - Devices"]
)
class DeviceTelemetryModuleLinkView(APIView):
    """Associa um módulo de telemetria a um device"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTelemetryModuleLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_id = serializer.validated_data['device_id']
        module_id = serializer.validated_data['module_id']
        
        device = get_object_or_404(Device, id=device_id)
        module = get_object_or_404(TelemetryModule, id=module_id)
        
        # Verificar se já existe uma associação ativa
        existing_link = DeviceTelemetryModule.objects.filter(
            device=device, 
            module=module, 
            is_linked=True
        ).first()
        
        if existing_link:
            return Response(
                {"detail": "Associação já existe entre este device e módulo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Desativar qualquer associação anterior do módulo
        DeviceTelemetryModule.objects.filter(
            module=module,
            is_linked=True
        ).update(is_linked=False, unlinked_at=timezone.now())
        
        # Desativar qualquer associação anterior do device
        DeviceTelemetryModule.objects.filter(
            device=device,
            is_linked=True
        ).update(is_linked=False, unlinked_at=timezone.now())
        
        # Criar nova associação
        link = DeviceTelemetryModule.objects.create(
            device=device,
            module=module,
            linked_at=timezone.now()
        )
        
        response_serializer = DeviceTelemetryModuleSerializer(link)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)