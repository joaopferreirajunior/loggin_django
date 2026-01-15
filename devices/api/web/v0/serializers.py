from rest_framework import serializers
from devices.models import Device, TelemetryModule, DeviceTelemetryModule, DeviceLocation, DeviceEvent
from drf_spectacular.utils import extend_schema_serializer


@extend_schema_serializer(component_name="WebDevice")
class DeviceSerializer(serializers.ModelSerializer):
    """Serializer básico para Device"""
    telemetry_module = serializers.SerializerMethodField()
    locked_at = serializers.SerializerMethodField()
    tested_at = serializers.SerializerMethodField()
    sent_at = serializers.SerializerMethodField()
    sold_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'serial', 'model', 'locked', 'locked_at', 
            'tested', 'tested_at', 'sent', 'sent_at', 'sold', 'sold_at', 
            'is_active', 'created', 'modified', 'telemetry_module'
        ]
    
    def get_locked_at(self, obj):
        """Retorna created_at do último evento de locked"""
        event = obj.events.filter(event='locked').first()
        return event.created_at if event else None
    
    def get_tested_at(self, obj):
        """Retorna created_at do último evento de tested"""
        event = obj.events.filter(event='tested').first()
        return event.created_at if event else None
    
    def get_sent_at(self, obj):
        """Retorna created_at do último evento de sent"""
        event = obj.events.filter(event='sent').first()
        return event.created_at if event else None
    
    def get_sold_at(self, obj):
        """Retorna created_at do último evento de sold"""
        event = obj.events.filter(event='sold').first()
        return event.created_at if event else None
    
    def get_telemetry_module(self, obj):
        """Retorna informações do módulo de telemetria vinculado"""
        module = obj.get_current_telemetry_module()
        if module:
            return {
                'id': module.id,
                'imei': module.imei,
                'icc_id': module.icc_id,
                'modelo': module.modelo
            }
        return None


@extend_schema_serializer(component_name="WebTelemetryModule")
class TelemetryModuleSerializer(serializers.ModelSerializer):
    """Serializer para TelemetryModule"""
    current_device = serializers.SerializerMethodField()
    
    class Meta:
        model = TelemetryModule
        fields = [
            'id', 'imei', 'icc_id', 'modelo', 'current_device',
            'last_online_at', 'is_active', 'created', 'modified'
        ]
    
    def get_current_device(self, obj):
        """Retorna informações básicas do device atual"""
        device = obj.get_current_device()
        if device:
            return {
                'id': device.id,
                'serial': device.serial,
                'model': device.model
            }
        return None


@extend_schema_serializer(component_name="WebDeviceTelemetryModule")
class DeviceTelemetryModuleSerializer(serializers.ModelSerializer):
    """Serializer para relacionamento Device-TelemetryModule"""
    device_info = serializers.SerializerMethodField()
    module_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceTelemetryModule
        fields = [
            'id', 'device', 'module', 'device_info', 'module_info',
            'linked_at', 'unlinked_at', 'is_linked'
        ]
    
    def get_device_info(self, obj):
        """Informações básicas do device"""
        return {
            'id': obj.device.id,
            'serial': obj.device.serial,
            'model': obj.device.model
        }
    
    def get_module_info(self, obj):
        """Informações básicas do módulo"""
        return {
            'id': obj.module.id,
            'imei': obj.module.imei,
            'modelo': obj.module.modelo
        }


@extend_schema_serializer(component_name="WebDeviceCreate")
class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de Device"""
    
    class Meta:
        model = Device
        fields = ['serial', 'model']
    
    def validate_serial(self, value):
        """Validação customizada para serial único"""
        if Device.objects.filter(serial=value, is_active=True).exists():
            raise serializers.ValidationError("Já existe um device ativo com este serial.")
        return value


@extend_schema_serializer(component_name="WebTelemetryModuleCreate")
class TelemetryModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de TelemetryModule"""
    
    class Meta:
        model = TelemetryModule
        fields = ['imei', 'icc_id', 'modelo']
    
    def validate_imei(self, value):
        """Validação customizada para IMEI único"""
        if TelemetryModule.objects.filter(imei=value, is_active=True).exists():
            raise serializers.ValidationError("Já existe um módulo ativo com este IMEI.")
        return value


@extend_schema_serializer(component_name="WebDeviceTelemetryModuleLink")
class DeviceTelemetryModuleLinkSerializer(serializers.ModelSerializer):
    """Serializer para vinculação Device-TelemetryModule"""
    
    class Meta:
        model = DeviceTelemetryModule
        fields = ['device', 'module']
    
    def validate(self, data):
        """Validar se já existe vínculo ativo"""
        device = data.get('device')
        module = data.get('module')
        
        # Verificar se o device já tem um módulo vinculado
        if device.has_telemetry_module():
            current_module = device.get_current_telemetry_module()
            raise serializers.ValidationError(
                f"Device já possui módulo vinculado (IMEI: {current_module.imei}). "
                "Desvincule primeiro para vincular outro."
            )
        
        # Verificar se o módulo já está vinculado a outro device
        if module.is_linked_to_device():
            current_device = module.get_current_device()
            raise serializers.ValidationError(
                f"Módulo já está vinculado ao device {current_device.serial}. "
                "Desvincule primeiro para vincular a outro device."
            )
        
        return data
    
    def create(self, validated_data):
        """Criar vinculação usando método do device"""
        device = validated_data['device']
        module = validated_data['module']
        return device.link_telemetry_module(module)

@extend_schema_serializer(component_name="WebDeviceLocationCreate")
class DeviceLocationCreateSerializer(serializers.Serializer):
    """Serializer para criação de localização de device"""
    serial = serializers.CharField(required=False, allow_blank=True, help_text="Serial do device (opcional)")
    imei = serializers.CharField(required=False, allow_blank=True, help_text="IMEI do módulo de telemetria (opcional)")
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    read_at = serializers.DateTimeField(required=True, help_text="Timestamp da leitura (obrigatório)")
    
    def validate(self, data):
        """Validar que pelo menos serial ou imei foi informado"""
        serial = data.get('serial', '').strip()
        imei = data.get('imei', '').strip()
        
        if not serial and not imei:
            raise serializers.ValidationError(
                "Pelo menos um dos campos 'serial' ou 'imei' deve ser informado."
            )
        
        return data
    
    def validate_latitude(self, value):
        """Validar range de latitude"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude deve estar entre -90 e 90.")
        return value
    
    def validate_longitude(self, value):
        """Validar range de longitude"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude deve estar entre -180 e 180.")
        return value


@extend_schema_serializer(component_name="WebDeviceLocation")
class DeviceLocationSerializer(serializers.ModelSerializer):
    """Serializer para resposta de DeviceLocation"""
    device_serial = serializers.CharField(source='device.serial', read_only=True, allow_null=True)
    module_imei = serializers.CharField(source='module.imei', read_only=True, allow_null=True)
    
    class Meta:
        model = DeviceLocation
        fields = ['id', 'device', 'device_serial', 'module', 'module_imei', 'latitude', 'longitude', 'read_at']

@extend_schema_serializer(component_name="WebDeviceGlobalLocation")
class DeviceGlobalLocationSerializer(serializers.Serializer):
    """Serializer para localização global de devices"""
    serial = serializers.CharField()
    model = serializers.CharField()
    imei = serializers.CharField(allow_null=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    last_online_at = serializers.DateTimeField(allow_null=True)
    locked = serializers.BooleanField()
    tested = serializers.BooleanField()
    sent = serializers.BooleanField()
    sold = serializers.BooleanField()


@extend_schema_serializer(component_name="WebDeviceEventCreate")
class DeviceEventCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de eventos de device"""
    
    class Meta:
        model = DeviceEvent
        fields = ['event']
    
    def validate_event(self, value):
        """Valida se o tipo de evento é permitido"""
        allowed_events = ['sold', 'sent', 'tested', 'locked', 'unlocked']
        if value not in allowed_events:
            raise serializers.ValidationError(
                f"Evento inválido. Valores permitidos: {', '.join(allowed_events)}"
            )
        return value


@extend_schema_serializer(component_name="WebDeviceEvent")
class DeviceEventSerializer(serializers.ModelSerializer):
    """Serializer para resposta de DeviceEvent"""
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    device_serial = serializers.CharField(source='device.serial', read_only=True)
    
    class Meta:
        model = DeviceEvent
        fields = ['id', 'device', 'device_serial', 'event', 'created_at', 'user_email']
        read_only_fields = ['id', 'device', 'device_serial', 'created_at', 'user_email']


@extend_schema_serializer(
    component_name="WebDeviceWithTelemetryCreate",
    examples=[
        {
            "serial": "ABC123XYZ456",
            "model": "Model X Pro",
            "imei": "123456789012345",
            "icc_id": "12345678901234567890",
            "gps_model": "GPS-V1"
        }
    ]
)
class DeviceWithTelemetryCreateSerializer(serializers.Serializer):
    """Serializer para criar device + telemetry module + associação em uma única requisição"""
    
    # Campos do Device
    serial = serializers.CharField(
        max_length=22,
        help_text="Número de série do device. Se já existir, usa o device existente."
    )
    model = serializers.CharField(
        max_length=24,
        default="undefined",
        help_text="Modelo do device (ex: Model X Pro, Device V2)"
    )
    
    # Campos do TelemetryModule
    imei = serializers.CharField(
        max_length=16,
        help_text="IMEI do módulo de telemetria (15 dígitos). Se já existir, usa o módulo existente."
    )
    icc_id = serializers.CharField(
        max_length=20,
        help_text="Identificador ICC do chip SIM (ICCID - até 20 dígitos)"
    )
    gps_model = serializers.CharField(
        max_length=12,
        help_text="Modelo do módulo GPS/telemetria (ex: GPS-V1, Tracker-X)"
    )
    
    def create(self, validated_data):
        """Cria ou recupera device e module, e cria a associação"""
        from django.utils import timezone
        
        # Extrai dados do device
        device_data = {
            'serial': validated_data['serial'],
            'model': validated_data.get('model', 'undefined')
        }
        
        # Extrai dados do module
        module_data = {
            'imei': validated_data['imei'],
            'icc_id': validated_data['icc_id'],
            'modelo': validated_data['gps_model']  # API usa 'gps_model', model usa 'modelo'
        }
        
        # Cria ou recupera device pelo serial
        device, device_created = Device.objects.get_or_create(
            serial=device_data['serial'],
            defaults=device_data
        )
        
        # Cria ou recupera module pelo imei
        module, module_created = TelemetryModule.objects.get_or_create(
            imei=module_data['imei'],
            defaults=module_data
        )
        
        # Verifica se já existe uma associação ativa
        existing_link = DeviceTelemetryModule.objects.filter(
            device=device,
            module=module,
            is_linked=True
        ).first()
        
        if not existing_link:
            # Desativa qualquer link anterior do device
            DeviceTelemetryModule.objects.filter(
                device=device,
                is_linked=True
            ).update(is_linked=False, unlinked_at=timezone.now())
            
            # Desativa qualquer link anterior do module
            DeviceTelemetryModule.objects.filter(
                module=module,
                is_linked=True
            ).update(is_linked=False, unlinked_at=timezone.now())
            
            # Cria nova associação
            link = DeviceTelemetryModule.objects.create(
                device=device,
                module=module,
                linked_at=timezone.now(),
                is_linked=True
            )
        else:
            link = existing_link
        
        return {
            'device': device,
            'module': module,
            'link': link,
            'device_created': device_created,
            'module_created': module_created
        }


@extend_schema_serializer(
    component_name="WebDeviceWithTelemetryResponse",
    examples=[
        {
            "device": {
                "id": 1,
                "serial": "ABC123XYZ456",
                "model": "Model X Pro",
                "locked": False,
                "tested": False,
                "sent": False,
                "sold": False
            },
            "module": {
                "id": 1,
                "imei": "123456789012345",
                "icc_id": "12345678901234567890",
                "modelo": "GPS-V1"
            },
            "device_created": True,
            "module_created": True,
            "link_id": 1
        }
    ]
)
class DeviceWithTelemetryResponseSerializer(serializers.Serializer):
    """Serializer para resposta da criação de device + telemetry module"""
    device = DeviceSerializer(
        help_text="Dados completos do device criado ou recuperado"
    )
    module = TelemetryModuleSerializer(
        help_text="Dados completos do módulo de telemetria criado ou recuperado"
    )
    device_created = serializers.BooleanField(
        help_text="True se o device foi criado, False se já existia"
    )
    module_created = serializers.BooleanField(
        help_text="True se o módulo foi criado, False se já existia"
    )
    link_id = serializers.IntegerField(
        help_text="ID da associação entre device e módulo de telemetria"
    )
