from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from devices.models import Device, TelemetryModule, DeviceTelemetryModule, DeviceLocation, DeviceEvent
from .serializers import (
    MobileDeviceSerializer, MobileDeviceCreateSerializer, MobileTelemetryModuleSerializer,
    MobileTelemetryModuleCreateSerializer, MobileDeviceTelemetryModuleSerializer,
    MobileDeviceTelemetryModuleLinkSerializer, MobileDeviceLocationCreateSerializer,
    MobileDeviceLocationSerializer, MobileDeviceGlobalLocationSerializer,
    MobileDeviceEventCreateSerializer, MobileDeviceEventSerializer
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
    operation_id="mobile_create_device_event",
    summary="Criar evento de device (Mobile)",
    description="Cria um evento de device (sold, sent, tested, locked, unlocked) e atualiza automaticamente o status do device",
    request=MobileDeviceEventCreateSerializer,
    responses={
        201: MobileDeviceEventSerializer,
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceEventCreateView(APIView):
    """Cria eventos de device via mobile"""
    permission_classes = [IsAuthenticated]

    def post(self, request, deviceId):
        device = get_object_or_404(Device, id=deviceId)
        
        serializer = MobileDeviceEventCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Criar evento vinculado ao device e ao usuário
            event = serializer.save(device=device, user=request.user)
            
            # Retornar evento criado
            response_serializer = MobileDeviceEventSerializer(event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="mobile_list_device_events",
    summary="Listar eventos de device (Mobile)",
    description="Lista todos os eventos de um device específico ordenados por data (mais recente primeiro)",
    responses={
        200: MobileDeviceEventSerializer(many=True),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceEventListView(generics.ListAPIView):
    """Lista eventos de um device via mobile"""
    serializer_class = MobileDeviceEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        device_id = self.kwargs['deviceId']
        device = get_object_or_404(Device, id=device_id)
        return device.events.all()


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
    operation_id="mobile_get_device_detail",
    summary="Consultar device específico (Mobile)",
    description="Retorna os detalhes de um device específico pelo deviceId via interface mobile",
    responses={
        200: MobileDeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceDetailView(APIView):
    """Consulta os detalhes de um device específico via mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request, deviceId):
        device = get_object_or_404(Device, id=deviceId, is_active=True)
        serializer = MobileDeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="mobile_get_telemetry_module_detail",
    summary="Consultar módulo de telemetria específico (Mobile)",
    description="Retorna os detalhes de um módulo de telemetria específico pelo moduleId via interface mobile",
    responses={
        200: MobileTelemetryModuleSerializer,
        404: OpenApiResponse(description="Módulo não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileTelemetryModuleDetailView(APIView):
    """Consulta os detalhes de um módulo de telemetria específico via mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request, moduleId):
        module = get_object_or_404(TelemetryModule, id=moduleId, is_active=True)
        serializer = MobileTelemetryModuleSerializer(module)
        return Response(serializer.data)


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

@extend_schema(
    operation_id="mobile_create_device_location",
    summary="Criar registro de localização (Mobile)",
    description=(
        "Cria um registro de localização para um device via interface mobile. "
        "Serial e IMEI são opcionais, mas pelo menos um deve ser informado."
    ),
    request=MobileDeviceLocationCreateSerializer,
    responses={
        201: MobileDeviceLocationSerializer,
        400: OpenApiResponse(description="Dados inválidos ou readAt não informado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceLocationCreateView(APIView):
    """Cria um registro de localização de device via mobile"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MobileDeviceLocationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serial = serializer.validated_data.get("serial", "").strip()
        imei = serializer.validated_data.get("imei", "").strip()
        latitude = serializer.validated_data["latitude"]
        longitude = serializer.validated_data["longitude"]
        read_at = serializer.validated_data["read_at"]
        
        device = None
        module = None
        
        # Caso 1: Ambos informados
        if serial and imei:
            try:
                device = Device.objects.get(serial=serial, is_active=True)
            except Device.DoesNotExist:
                return Response(
                    {"detail": f"Device com serial '{serial}' não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                module = TelemetryModule.objects.get(imei=imei, is_active=True)
            except TelemetryModule.DoesNotExist:
                return Response(
                    {"detail": f"Módulo com IMEI '{imei}' não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Caso 2: Apenas serial informado
        elif serial and not imei:
            try:
                device = Device.objects.get(serial=serial, is_active=True)
            except Device.DoesNotExist:
                return Response(
                    {"detail": f"Device com serial '{serial}' não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Buscar módulo linkado ao device (mais recente)
            module = device.get_current_telemetry_module()
        
        # Caso 3: Apenas imei informado
        elif imei and not serial:
            try:
                module = TelemetryModule.objects.get(imei=imei, is_active=True)
            except TelemetryModule.DoesNotExist:
                return Response(
                    {"detail": f"Módulo com IMEI '{imei}' não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Buscar device linkado ao módulo (mais recente)
            device = module.get_current_device()
        
        # Criar localização
        location = DeviceLocation.objects.create(
            device=device,
            module=module,
            latitude=latitude,
            longitude=longitude,
            read_at=read_at
        )
        
        response_serializer = MobileDeviceLocationSerializer(location)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



@extend_schema(
    operation_id="mobile_get_devices_global_locations",
    summary="Listar localização global de devices (Mobile)",
    description=(
        "Retorna a localização mais recente de cada device ativo que possui localização registrada via interface mobile."
    ),
    responses={
        200: MobileDeviceGlobalLocationSerializer(many=True)
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceGlobalLocationsView(APIView):
    """Lista localização global de todos os devices ativos com localização via mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Prefetch, Max
        
        # Buscar devices ativos que possuem localizações
        devices = Device.objects.filter(
            is_active=True,
            locations__isnull=False
        ).distinct().prefetch_related(
            'locations',
            'telemetry_links',
            'telemetry_links__module'
        )
        
        result = []
        
        for device in devices:
            # Pegar localização mais recente
            latest_location = device.locations.order_by('-read_at').first()
            
            if not latest_location:
                continue
            
            # Pegar módulo linkado atualmente
            current_module = device.get_current_telemetry_module()
            
            imei = None
            last_online_at = None
            
            if current_module:
                imei = current_module.imei
                last_online_at = current_module.last_online_at
            else:
                # Buscar último link (mais recente)
                last_link = device.telemetry_links.order_by('-linked_at').first()
                if last_link and last_link.module:
                    last_online_at = last_link.module.last_online_at
            
            result.append({
                'serial': device.serial,
                'model': device.model,
                'imei': imei,
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'last_online_at': last_online_at,
                'locked': device.locked,
                'tested': device.tested,
                'sold': device.sold
            })
        
        serializer = MobileDeviceGlobalLocationSerializer(result, many=True)
        return Response(serializer.data)


@extend_schema(
    operation_id="mobile_get_device_locations",
    summary="Listar últimas localizações de um device (Mobile)",
    description="Retorna as 10 últimas localizações de um device específico ordenadas por data (mais recente primeiro)",
    responses={
        200: MobileDeviceLocationSerializer(many=True),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Mobile - Devices"]
)
class MobileDeviceLocationsListView(APIView):
    """Lista as 10 últimas localizações de um device específico via mobile"""
    permission_classes = [IsAuthenticated]

    def get(self, request, deviceId):
        device = get_object_or_404(Device, id=deviceId, is_active=True)
        
        # Buscar as 10 últimas localizações do device
        locations = DeviceLocation.objects.filter(
            device=device
        ).order_by('-read_at')[:10]
        
        serializer = MobileDeviceLocationSerializer(locations, many=True)
        return Response(serializer.data)
