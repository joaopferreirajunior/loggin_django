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
    DeviceEvent, DeviceModel, DeviceFeatures, DeviceLease
)
from .serializers import (
    DeviceSerializer, DeviceDetailSerializer, DeviceCreateSerializer, 
    TelemetryModuleSerializer, TelemetryModuleCreateSerializer, 
    DeviceTelemetryModuleSerializer, DeviceTelemetryModuleLinkSerializer,
    DeviceLocationCreateSerializer, DeviceLocationSerializer, 
    DeviceGlobalLocationSerializer, DeviceEventCreateSerializer, 
    DeviceEventSerializer, DeviceWithTelemetryCreateSerializer, 
    DeviceWithTelemetryResponseSerializer, LocationsResponseSerializer,
    DeviceModelSerializer, DeviceFeaturesSerializer, DeviceLeaseSerializer
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
        location_data = {
            'device': device,
            'module': module,
            'latitude': latitude,
            'longitude': longitude,
            'read_at': read_at
        }
        
        # Adicionar campos opcionais se fornecidos
        optional_fields = ['speed', 'accuracy', 'is_moving', 'course', 'altitude', 'battery', 'signal_strength']
        for field in optional_fields:
            if field in serializer.validated_data:
                location_data[field] = serializer.validated_data[field]
        
        location = DeviceLocation.objects.create(**location_data)
        
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
                'model': device.device_model.name if device.device_model else None,
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


@extend_schema(
    operation_id="create_device_with_telemetry",
    summary="Criar device com módulo de telemetria",
    description="""
    Cria ou recupera um device e módulo de telemetria GPS, criando automaticamente a associação entre eles.
    
    **Comportamento:**
    - Se o `serial` já existir no sistema, usa o device existente (não cria novo)
    - Se o `imei` já existir no sistema, usa o módulo existente (não cria novo)
    - Desvincula qualquer associação anterior do device com outros módulos
    - Desvincula qualquer associação anterior do módulo com outros devices
    - Cria uma nova associação ativa entre o device e o módulo
    
    **Casos de uso:**
    1. Registrar um novo device com novo módulo GPS
    2. Vincular um módulo GPS existente a um device existente
    3. Trocar o módulo GPS de um device
    4. Reatribuir um módulo GPS para outro device
    
    **Campos obrigatórios:**
    - `serial`: Número de série único do device
    - `imei`: IMEI do módulo GPS (15 dígitos)
    - `icc_id`: ICCID do chip SIM do módulo
    - `gps_model`: Modelo do módulo GPS
    
    **Campos opcionais:**
    - `model`: Modelo do device (padrão: "undefined")
    
    **Resposta:**
    - `device_created`: Indica se um novo device foi criado (true) ou se já existia (false)
    - `module_created`: Indica se um novo módulo foi criado (true) ou se já existia (false)
    - `link_id`: ID da nova associação criada entre device e módulo
    """,
    request=DeviceWithTelemetryCreateSerializer,
    responses={
        201: DeviceWithTelemetryResponseSerializer,
        400: OpenApiResponse(description="Dados inválidos - verifique os campos obrigatórios e formatos")
    },
    tags=["Web - Devices"]
)
class DeviceWithTelemetryCreateView(APIView):
    """Cria device + telemetry module + associação em uma única requisição"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceWithTelemetryCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            result = serializer.save()
            
            # Preparar resposta
            response_data = {
                'device': result['device'],
                'module': result['module'],
                'device_created': result['device_created'],
                'module_created': result['module_created'],
                'link_id': result['link'].id
            }
            
            response_serializer = DeviceWithTelemetryResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="get_all_locations",
    summary="Listar todas as localizações de devices",
    description="""
    Retorna a última localização de todos os devices com seus dados de telemetria.
    
    **Formato de resposta:**
    - `success`: Indica se a requisição foi bem-sucedida
    - `data`: Array com as localizações e dados dos devices
    - `meta`: Metadados da resposta (timestamp, contadores)
    
    **Dados retornados para cada localização:**
    - Informações de posição (latitude, longitude, speed, etc)
    - Dados do device (serial, model, locked status)
    - Dados do módulo GPS (IMEI, modelo)
    - Dados de telemetria (bateria, sinal, altitude, etc)
    """,
    responses={
        200: LocationsResponseSerializer,
    },
    tags=["Web - Devices"]
)
class DeviceLocationsView(APIView):
    """Lista todas as localizações de devices"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from django.db.models import Prefetch
        
        # Buscar devices ativos com suas últimas localizações
        devices = Device.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'locations',
                queryset=DeviceLocation.objects.select_related('module').order_by('-read_at')[:1],
                to_attr='latest_location_list'
            ),
            Prefetch(
                'telemetry_links',
                queryset=DeviceTelemetryModule.objects.filter(is_linked=True).select_related('module'),
                to_attr='active_telemetry_links'
            )
        )
        
        data = []
        
        for device in devices:
            # Pegar a última localização
            if not device.latest_location_list:
                continue
                
            location = device.latest_location_list[0]
            
            # Pegar módulo linkado
            module = None
            if device.active_telemetry_links:
                module = device.active_telemetry_links[0].module
            elif location.module:
                module = location.module
            
            # Se não tem módulo, pular
            if not module:
                continue
            
            # Montar device_metadata
            device_metadata = {
                'name': None,
                'brand': None,
                'model': device.device_model.name if device.device_model else None,
                'serial': device.serial,
                'imei': module.imei,
                'locked': device.locked,
                'state': None,
                'city': None
            }
            
            # Montar dados da localização
            location_data = {
                'id': f'pos_{location.id}',
                'device_id': module.imei,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'speed': location.speed,
                'accuracy': location.accuracy,
                'is_moving': location.is_moving,
                'created_at': device.created,
                'inserted_at': location.read_at,
                'kind': module.modelo,
                'device_metadata': device_metadata,
                'course': location.course,
                'altitude': location.altitude,
                'battery': location.battery,
                'signal_strength': location.signal_strength
            }
            
            data.append(location_data)
        
        # Calcular metadados
        total_devices = Device.objects.filter(is_active=True).count()
        active_devices = Device.objects.filter(is_active=True, locked=False).count()
        
        response_data = {
            'success': True,
            'data': data,
            'meta': {
                'last_updated': timezone.now(),
                'active_devices': active_devices,
                'total_devices': total_devices
            }
        }
        
        serializer = LocationsResponseSerializer(response_data)
        return Response(serializer.data)


# ============================================
# VIEWSETS REST - DeviceModel, DeviceFeatures, DeviceLease, Device
# ============================================

@extend_schema(tags=["Web - Devices"])
class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de Device
    
    list: GET /api/web/v0/devices/ - Lista todos os devices
    retrieve: GET /api/web/v0/devices/{id}/ - Detalhes de um device (básico - SEM files)
    create: POST /api/web/v0/devices/ - Criar novo device
    update: PUT /api/web/v0/devices/{id}/ - Atualizar device completo
    partial_update: PATCH /api/web/v0/devices/{id}/ - Atualizar device parcial
    destroy: DELETE /api/web/v0/devices/{id}/ - Deletar device
    details: GET /api/web/v0/devices/{id}/details/ - Detalhes completos (COM files do deviceFeatures)
    lease: GET /api/web/v0/devices/{id}/lease/ - Retorna lease ativo do device
    """
    queryset = Device.objects.filter(is_active=True).select_related('device_model')
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="device_details",
        summary="Detalhes completos do device",
        description="Retorna informações completas do device incluindo files no deviceFeatures",
        responses={200: DeviceDetailSerializer},
        tags=["Web - Devices"]
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Retorna detalhes completos do device COM files"""
        device = self.get_object()
        serializer = DeviceDetailSerializer(device)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id="device_lease",
        summary="Lease ativo do device",
        description="Retorna o lease atualmente ativo do device (se houver)",
        responses={
            200: DeviceLeaseSerializer,
            404: OpenApiResponse(description="Nenhum lease ativo encontrado")
        },
        tags=["Web - Devices"]
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
        
        serializer = DeviceLeaseSerializer(active_lease)
        return Response(serializer.data)


# ============================================
# VIEWSETS PARA NOVOS MODELOS
# ============================================

@extend_schema(tags=["Web - Device Models"])
class DeviceModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de DeviceModel (catálogo de modelos)
    
    list: GET /api/web/v0/device-models/ - Lista todos os modelos
    retrieve: GET /api/web/v0/device-models/{id}/ - Detalhes de um modelo
    create: POST /api/web/v0/device-models/ - Criar novo modelo
    update: PUT /api/web/v0/device-models/{id}/ - Atualizar modelo completo
    partial_update: PATCH /api/web/v0/device-models/{id}/ - Atualizar modelo parcial
    destroy: DELETE /api/web/v0/device-models/{id}/ - Deletar modelo
    features: GET /api/web/v0/device-models/{id}/features/ - Lista DeviceFeatures do modelo
    """
    queryset = DeviceModel.objects.filter(is_active=True)
    serializer_class = DeviceModelSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        operation_id="device_model_features",
        summary="Features do modelo",
        description="Lista todos os DeviceFeatures (arquivos/documentos) de um modelo específico",
        responses={200: DeviceFeaturesSerializer(many=True)},
        tags=["Web - Device Models"]
    )
    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        """Lista todas as features do modelo"""
        device_model = self.get_object()
        features = device_model.features.filter(is_active=True).order_by('order', 'title')
        serializer = DeviceFeaturesSerializer(features, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Web - Device Features"])
class DeviceFeaturesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de DeviceFeatures (arquivos/documentos dos modelos)
    
    list: GET /api/web/v0/device-features/ - Lista todas as features
    retrieve: GET /api/web/v0/device-features/{id}/ - Detalhes de uma feature
    create: POST /api/web/v0/device-features/ - Criar nova feature
    update: PUT /api/web/v0/device-features/{id}/ - Atualizar feature completo
    partial_update: PATCH /api/web/v0/device-features/{id}/ - Atualizar feature parcial
    destroy: DELETE /api/web/v0/device-features/{id}/ - Deletar feature
    """
    queryset = DeviceFeatures.objects.filter(is_active=True).select_related('device_model')
    serializer_class = DeviceFeaturesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Permite filtrar por device_model via query param"""
        queryset = super().get_queryset()
        device_model_id = self.request.query_params.get('device_model', None)
        if device_model_id:
            queryset = queryset.filter(device_model_id=device_model_id)
        return queryset.order_by('order', 'title')


@extend_schema(tags=["Web - Device Leases"])
class DeviceLeaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de DeviceLease (controle de aluguel)
    
    list: GET /api/web/v0/device-leases/ - Lista todos os leases
    retrieve: GET /api/web/v0/device-leases/{id}/ - Detalhes de um lease
    create: POST /api/web/v0/device-leases/ - Criar novo lease
    update: PUT /api/web/v0/device-leases/{id}/ - Atualizar lease completo
    partial_update: PATCH /api/web/v0/device-leases/{id}/ - Atualizar lease parcial
    destroy: DELETE /api/web/v0/device-leases/{id}/ - Deletar lease
    
    Filtros disponíveis:
    - device: filtra por ID do device (ex: ?device=1)
    """
    queryset = DeviceLease.objects.filter(is_active=True).select_related('device', 'user')
    serializer_class = DeviceLeaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Permite filtrar por device via query param"""
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('device', None)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset.order_by('-start_date')
