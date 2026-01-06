from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from devices.models import Device, TelemetryModule, DeviceTelemetryModule
from .serializers import (
    MobileDeviceSerializer, MobileDeviceCreateSerializer, MobileTelemetryModuleSerializer,
    MobileTelemetryModuleCreateSerializer, MobileDeviceTelemetryModuleSerializer,
    MobileDeviceTelemetryModuleLinkSerializer
)


@extend_schema(
    operation_id="mobile_create_device",
    summary="Criar device (Mobile)",
    description="Cria um novo device no sistema via interface mobile",
    request=MobileDeviceCreateSerializer,
    responses={
        201: MobileDeviceSerializer,
        400: OpenApiResponse(description="Dados inválidos")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceCreateView(generics.CreateAPIView):
    """Cria um novo device via mobile"""
    queryset = Device.objects.all()
    serializer_class = MobileDeviceCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        
        # Retornar o device criado com o serializer de resposta mobile
        response_serializer = MobileDeviceSerializer(device)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="mobile_test_device",
    summary="Marcar device como testado (Mobile)",
    description="Marca um device como testado via interface mobile",
    responses={
        200: MobileDeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceTestView(APIView):
    """Marca um device como testado via mobile"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, deviceId):
        device = get_object_or_404(Device, id=deviceId)
        
        # Marcar como testado
        device.tested = True
        device.tested_at = timezone.now()
        device.save()
        
        serializer = MobileDeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="mobile_sell_device",
    summary="Marcar device como vendido (Mobile)",
    description="Marca um device como vendido via interface mobile",
    responses={
        200: MobileDeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceSoldView(APIView):
    """Marca um device como vendido via mobile"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, deviceId):
        device = get_object_or_404(Device, id=deviceId)
        
        # Marcar como vendido
        device.sold = True
        device.sold_at = timezone.now()
        device.save()
        
        serializer = MobileDeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="mobile_create_telemetry_module",
    summary="Criar módulo de telemetria (Mobile)",
    description="Cria um novo módulo de telemetria via interface mobile",
    request=MobileTelemetryModuleCreateSerializer,
    responses={
        201: MobileTelemetryModuleSerializer,
        400: OpenApiResponse(description="Dados inválidos")
    },
    tags=["Mobile - Devices"]
)
class MobileTelemetryModuleCreateView(generics.CreateAPIView):
    """Cria um novo módulo de telemetria via mobile"""
    queryset = TelemetryModule.objects.all()
    serializer_class = MobileTelemetryModuleCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = serializer.save()
        
        # Retornar o módulo criado com o serializer de resposta mobile
        response_serializer = MobileTelemetryModuleSerializer(module)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="mobile_link_device_telemetry_module",
    summary="Associar módulo ao device (Mobile)",
    description="Cria uma associação entre um device e um módulo de telemetria via interface mobile",
    request=MobileDeviceTelemetryModuleLinkSerializer,
    responses={
        201: MobileDeviceTelemetryModuleSerializer,
        400: OpenApiResponse(description="Dados inválidos ou associação já existe")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceTelemetryModuleLinkView(APIView):
    """Associa um módulo de telemetria a um device via mobile"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MobileDeviceTelemetryModuleLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_id = serializer.validated_data['deviceId']
        module_id = serializer.validated_data['moduleId']
        
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
        
        response_serializer = MobileDeviceTelemetryModuleSerializer(link)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)