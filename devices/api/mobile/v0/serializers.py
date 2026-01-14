from rest_framework import serializers
from devices.models import Device, TelemetryModule, DeviceTelemetryModule, DeviceLocation, DeviceEvent
from drf_spectacular.utils import extend_schema_serializer


@extend_schema_serializer(component_name="MobileDevice")
class MobileDeviceSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Device mobile"""
    createdAt = serializers.DateTimeField(source='created', read_only=True)
    updatedAt = serializers.DateTimeField(source='modified', read_only=True)
    lockedAt = serializers.SerializerMethodField()
    testedAt = serializers.SerializerMethodField()
    sentAt = serializers.SerializerMethodField()
    soldAt = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    telemetryModule = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'serial', 'model', 'locked', 'lockedAt', 
            'tested', 'testedAt', 'sent', 'sentAt', 'sold', 'soldAt', 
            'isActive', 'createdAt', 'updatedAt', 'telemetryModule'
        ]
    
    def get_lockedAt(self, obj):
        """Retorna created_at do último evento de locked"""
        event = obj.events.filter(event='locked').first()
        return event.created_at if event else None
    
    def get_testedAt(self, obj):
        """Retorna created_at do último evento de tested"""
        event = obj.events.filter(event='tested').first()
        return event.created_at if event else None
    
    def get_sentAt(self, obj):
        """Retorna created_at do último evento de sent"""
        event = obj.events.filter(event='sent').first()
        return event.created_at if event else None
    
    def get_soldAt(self, obj):
        """Retorna created_at do último evento de sold"""
        event = obj.events.filter(event='sold').first()
        return event.created_at if event else None
    
    def get_telemetryModule(self, obj):
        """Retorna informações do módulo de telemetria vinculado"""
        module = obj.get_current_telemetry_module()
        if module:
            return {
                'id': module.id,
                'imei': module.imei,
                'iccId': module.icc_id,
                'modelo': module.modelo
            }
        return None


@extend_schema_serializer(component_name="MobileTelemetryModule")
class MobileTelemetryModuleSerializer(serializers.ModelSerializer):
    """Serializer mobile para TelemetryModule"""
    currentDevice = serializers.SerializerMethodField()
    iccId = serializers.CharField(source='icc_id', read_only=True)
    lastOnlineAt = serializers.DateTimeField(source='last_online_at', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='created', read_only=True)
    updatedAt = serializers.DateTimeField(source='modified', read_only=True)
    
    class Meta:
        model = TelemetryModule
        fields = [
            'id', 'imei', 'iccId', 'modelo', 'currentDevice',
            'lastOnlineAt', 'isActive', 'createdAt', 'updatedAt'
        ]
    
    def get_currentDevice(self, obj):
        """Retorna informações básicas do device atual"""
        device = obj.get_current_device()
        if device:
            return {
                'id': device.id,
                'serial': device.serial,
                'model': device.model
            }
        return None


@extend_schema_serializer(component_name="MobileDeviceTelemetryModule")
class MobileDeviceTelemetryModuleSerializer(serializers.ModelSerializer):
    """Serializer mobile para relacionamento Device-TelemetryModule"""
    deviceInfo = serializers.SerializerMethodField()
    moduleInfo = serializers.SerializerMethodField()
    linkedAt = serializers.DateTimeField(source='linked_at', read_only=True)
    unlinkedAt = serializers.DateTimeField(source='unlinked_at', read_only=True)
    isLinked = serializers.BooleanField(source='is_linked', read_only=True)
    
    class Meta:
        model = DeviceTelemetryModule
        fields = [
            'id', 'device', 'module', 'deviceInfo', 'moduleInfo',
            'linkedAt', 'unlinkedAt', 'isLinked'
        ]
    
    def get_deviceInfo(self, obj):
        """Informações básicas do device"""
        return {
            'id': obj.device.id,
            'serial': obj.device.serial,
            'model': obj.device.model
        }
    
    def get_moduleInfo(self, obj):
        """Informações básicas do módulo"""
        return {
            'id': obj.module.id,
            'imei': obj.module.imei,
            'modelo': obj.module.modelo
        }


@extend_schema_serializer(component_name="MobileDeviceCreate")
class MobileDeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer mobile para criação de Device"""
    
    class Meta:
        model = Device
        fields = ['serial', 'model']
    
    def validate_serial(self, value):
        """Validação customizada para serial único"""
        if Device.objects.filter(serial=value, is_active=True).exists():
            raise serializers.ValidationError("Já existe um device ativo com este serial.")
        return value


@extend_schema_serializer(component_name="MobileTelemetryModuleCreate")
class MobileTelemetryModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer mobile para criação de TelemetryModule"""
    iccId = serializers.CharField(source='icc_id')
    
    class Meta:
        model = TelemetryModule
        fields = ['imei', 'iccId', 'modelo']
    
    def validate_imei(self, value):
        """Validação customizada para IMEI único"""
        if TelemetryModule.objects.filter(imei=value, is_active=True).exists():
            raise serializers.ValidationError("Já existe um módulo ativo com este IMEI.")
        return value


@extend_schema_serializer(component_name="MobileDeviceTelemetryModuleLink")
class MobileDeviceTelemetryModuleLinkSerializer(serializers.ModelSerializer):
    """Serializer mobile para vinculação Device-TelemetryModule"""
    
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

@extend_schema_serializer(component_name="MobileDeviceLocationCreate")
class MobileDeviceLocationCreateSerializer(serializers.Serializer):
    """Serializer para criação de localização de device (mobile)"""
    serial = serializers.CharField(required=False, allow_blank=True, help_text="Serial do device (opcional)")
    imei = serializers.CharField(required=False, allow_blank=True, help_text="IMEI do módulo de telemetria (opcional)")
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    readAt = serializers.DateTimeField(source="read_at", required=True, help_text="Timestamp da leitura (obrigatório)")
    
    def validate(self, data):
        """Validar que pelo menos serial ou imei foi informado"""
        serial = data.get("serial", "").strip()
        imei = data.get("imei", "").strip()
        
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


@extend_schema_serializer(component_name="MobileDeviceLocation")
class MobileDeviceLocationSerializer(serializers.ModelSerializer):
    """Serializer para resposta de DeviceLocation (mobile)"""
    deviceSerial = serializers.CharField(source="device.serial", read_only=True, allow_null=True)
    moduleImei = serializers.CharField(source="module.imei", read_only=True, allow_null=True)
    readAt = serializers.DateTimeField(source="read_at", read_only=True)
    
    class Meta:
        model = DeviceLocation
        fields = ["id", "device", "deviceSerial", "module", "moduleImei", "latitude", "longitude", "readAt"]


@extend_schema_serializer(component_name="MobileDeviceGlobalLocation")
class MobileDeviceGlobalLocationSerializer(serializers.Serializer):
    """Serializer para localização global de devices (mobile)"""
    serial = serializers.CharField()
    model = serializers.CharField()
    imei = serializers.CharField(allow_null=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    lastOnlineAt = serializers.DateTimeField(source="last_online_at", allow_null=True)
    locked = serializers.BooleanField()
    tested = serializers.BooleanField()


@extend_schema_serializer(component_name="MobileDeviceEventCreate")
class MobileDeviceEventCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de eventos de device (mobile)"""
    
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


@extend_schema_serializer(component_name="MobileDeviceEvent")
class MobileDeviceEventSerializer(serializers.ModelSerializer):
    """Serializer para resposta de DeviceEvent (mobile)"""
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    userEmail = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    deviceSerial = serializers.CharField(source='device.serial', read_only=True)
    
    class Meta:
        model = DeviceEvent
        fields = ['id', 'device', 'deviceSerial', 'event', 'createdAt', 'userEmail']
        read_only_fields = ['id', 'device', 'deviceSerial', 'createdAt', 'userEmail']
