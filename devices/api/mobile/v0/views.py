from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from drf_spectacular.utils import extend_schema, OpenApiResponse
from devices.models import (
    Device, TelemetryModule, DeviceTelemetryModule, DeviceLocation,
    DeviceModel, DeviceFeatures, DeviceLease
)
from .serializers import (
    MobileDeviceSerializer, MobileDeviceDetailSerializer, MobileDeviceCreateSerializer,
    MobileTelemetryModuleSerializer, MobileTelemetryModuleCreateSerializer,
    MobileDeviceTelemetryModuleSerializer, MobileDeviceTelemetryModuleLinkSerializer,
    MobileDeviceLocationCreateSerializer, MobileDeviceLocationSerializer,
    MobileDeviceGlobalLocationSerializer, MobileDeviceModelSerializer,
    MobileDeviceFeaturesSerializer, MobileDeviceLeaseSerializer
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
                'model': device.device_model.name if device.device_model else None,
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


# ============================================
# VIEWSETS MOBILE PARA NOVOS MODELOS
# ============================================

@extend_schema(tags=["Mobile - Devices"])
class MobileDeviceViewSet(viewsets.ModelViewSet):
    """ViewSet mobile para CRUD de Device"""
    queryset = Device.objects.filter(is_active=True).select_related('device_model')
    serializer_class = MobileDeviceSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="mobile_device_details",
        summary="Detalhes completos do device (Mobile)",
        description="Retorna informações completas do device incluindo files no deviceFeatures",
        responses={200: MobileDeviceDetailSerializer},
        tags=["Mobile - Devices"]
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Retorna detalhes completos do device COM files"""
        device = self.get_object()
        serializer = MobileDeviceDetailSerializer(device)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id="mobile_device_lease",
        summary="Lease ativo do device (Mobile)",
        description="Retorna o lease atualmente ativo do device (se houver)",
        responses={
            200: MobileDeviceLeaseSerializer,
            404: OpenApiResponse(description="Nenhum lease ativo encontrado")
        },
        tags=["Mobile - Devices"]
    )
    @action(detail=True, methods=['get'])
    def lease(self, request, pk=None):
        """Retorna o lease ativo do device"""
        device = self.get_object()
        active_lease = device.leases.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        ).first()
        
        if not active_lease:
            return Response(
                {"detail": "Nenhum lease ativo encontrado para este device"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MobileDeviceLeaseSerializer(active_lease)
        return Response(serializer.data)


@extend_schema(tags=["Mobile - Device Models"])
class MobileDeviceModelViewSet(viewsets.ModelViewSet):
    """ViewSet mobile para CRUD de DeviceModel"""
    queryset = DeviceModel.objects.filter(is_active=True)
    serializer_class = MobileDeviceModelSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="mobile_device_model_features",
        summary="Features do modelo (Mobile)",
        description="Lista todos os DeviceFeatures (arquivos/documentos) de um modelo específico",
        responses={200: MobileDeviceFeaturesSerializer(many=True)},
        tags=["Mobile - Device Models"]
    )
    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        """Lista todas as features do modelo"""
        device_model = self.get_object()
        features = device_model.features.filter(is_active=True).order_by('order', 'title')
        serializer = MobileDeviceFeaturesSerializer(features, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Mobile - Device Features"])
class MobileDeviceFeaturesViewSet(viewsets.ModelViewSet):
    """ViewSet mobile para CRUD de DeviceFeatures"""
    queryset = DeviceFeatures.objects.filter(is_active=True).select_related('device_model')
    serializer_class = MobileDeviceFeaturesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Permite filtrar por deviceModel via query param"""
        queryset = super().get_queryset()
        device_model_id = self.request.query_params.get('deviceModel', None)
        if device_model_id:
            queryset = queryset.filter(device_model_id=device_model_id)
        return queryset.order_by('order', 'title')


@extend_schema(tags=["Mobile - Device Leases"])
class MobileDeviceLeaseViewSet(viewsets.ModelViewSet):
    """ViewSet mobile para CRUD de DeviceLease"""
    queryset = DeviceLease.objects.filter(is_active=True).select_related('device', 'user')
    serializer_class = MobileDeviceLeaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Permite filtrar por device via query param"""
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('device', None)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset.order_by('-start_date')
