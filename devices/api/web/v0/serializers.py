from rest_framework import serializers
from devices.models import Device, TelemetryModule, DeviceTelemetryModule
from drf_spectacular.utils import extend_schema_serializer


@extend_schema_serializer(component_name="WebDevice")
class DeviceSerializer(serializers.ModelSerializer):
    """Serializer básico para Device"""
    telemetry_module = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'serial', 'model', 'locked', 'locked_at', 
            'tested', 'tested_at', 'sold', 'sold_at', 
            'is_active', 'created', 'modified', 'telemetry_module'
        ]
    
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
            'is_active', 'created', 'modified'
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