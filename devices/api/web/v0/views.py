from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from devices.models import Device, TelemetryModule, DeviceTelemetryModule, DeviceLocation, DeviceEvent
from .serializers import (
    DeviceSerializer, DeviceCreateSerializer, TelemetryModuleSerializer, 
    TelemetryModuleCreateSerializer, DeviceTelemetryModuleSerializer,
    DeviceTelemetryModuleLinkSerializer, DeviceLocationCreateSerializer,
    DeviceLocationSerializer, DeviceGlobalLocationSerializer,
    DeviceEventCreateSerializer, DeviceEventSerializer
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
    operation_id="create_device_event",
    summary="Criar evento de device",
    description="Cria um evento de device (sold, sent, tested, locked, unlocked) e atualiza automaticamente o status do device",
    request=DeviceEventCreateSerializer,
    responses={
        201: DeviceEventSerializer,
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceEventCreateView(APIView):
    """Cria eventos de device"""
    permission_classes = [IsAuthenticated]

    def post(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        
        serializer = DeviceEventCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Criar evento vinculado ao device e ao usuário
            event = serializer.save(device=device, user=request.user)
            
            # Retornar evento criado
            response_serializer = DeviceEventSerializer(event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="list_device_events",
    summary="Listar eventos de device",
    description="Lista todos os eventos de um device específico ordenados por data (mais recente primeiro)",
    responses={
        200: DeviceEventSerializer(many=True),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceEventListView(generics.ListAPIView):
    """Lista eventos de um device"""
    serializer_class = DeviceEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        device_id = self.kwargs['device_id']
        device = get_object_or_404(Device, id=device_id)
        return device.events.all()


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
    operation_id="get_device_detail",
    summary="Consultar device específico",
    description="Retorna os detalhes de um device específico pelo device_id",
    responses={
        200: DeviceSerializer,
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceDetailView(APIView):
    """Consulta os detalhes de um device específico"""
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id, is_active=True)
        serializer = DeviceSerializer(device)
        return Response(serializer.data)


@extend_schema(
    operation_id="get_telemetry_module_detail",
    summary="Consultar módulo de telemetria específico",
    description="Retorna os detalhes de um módulo de telemetria específico pelo module_id",
    responses={
        200: TelemetryModuleSerializer,
        404: OpenApiResponse(description="Módulo não encontrado")
    },
    tags=["Web - Devices"]
)
class TelemetryModuleDetailView(APIView):
    """Consulta os detalhes de um módulo de telemetria específico"""
    permission_classes = [IsAuthenticated]

    def get(self, request, module_id):
        module = get_object_or_404(TelemetryModule, id=module_id, is_active=True)
        serializer = TelemetryModuleSerializer(module)
        return Response(serializer.data)


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

@extend_schema(
    operation_id="create_device_location",
    summary="Criar registro de localização",
    description=(
        "Cria um registro de localização para um device. "
        "Serial e IMEI são opcionais, mas pelo menos um deve ser informado. "
        "Se apenas serial: busca device e pega módulo linkado. "
        "Se apenas imei: busca módulo e pega device linkado. "
        "Se ambos: usa ambos diretamente."
    ),
    request=DeviceLocationCreateSerializer,
    responses={
        201: DeviceLocationSerializer,
        400: OpenApiResponse(description="Dados inválidos ou read_at não informado")
    },
    tags=["Web - Devices"]
)
class DeviceLocationCreateView(APIView):
    """Cria um registro de localização de device"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceLocationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serial = serializer.validated_data.get('serial', '').strip()
        imei = serializer.validated_data.get('imei', '').strip()
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        read_at = serializer.validated_data['read_at']
        
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
        
        response_serializer = DeviceLocationSerializer(location)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="get_devices_global_locations",
    summary="Listar localização global de devices",
    description=(
        "Retorna a localização mais recente de cada device ativo que possui localização registrada. "
        "Inclui informações do device, módulo linkado e última localização conhecida."
    ),
    responses={
        200: DeviceGlobalLocationSerializer(many=True)
    },
    tags=["Web - Devices"]
)
class DeviceGlobalLocationsView(APIView):
    """Lista localização global de todos os devices ativos com localização"""
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
        
        serializer = DeviceGlobalLocationSerializer(result, many=True)
        return Response(serializer.data)


@extend_schema(
    operation_id="get_device_locations",
    summary="Listar últimas localizações de um device",
    description="Retorna as 10 últimas localizações de um device específico ordenadas por data (mais recente primeiro)",
    responses={
        200: DeviceLocationSerializer(many=True),
        404: OpenApiResponse(description="Device não encontrado")
    },
    tags=["Web - Devices"]
)
class DeviceLocationsListView(APIView):
    """Lista as 10 últimas localizações de um device específico"""
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id, is_active=True)
        
        # Buscar as 10 últimas localizações do device
        locations = DeviceLocation.objects.filter(
            device=device
        ).order_by('-read_at')[:10]
        
        serializer = DeviceLocationSerializer(locations, many=True)
        return Response(serializer.data)
