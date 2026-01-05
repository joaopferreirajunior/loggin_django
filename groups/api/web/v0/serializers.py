from rest_framework import serializers
from groups.models import Group, Clinic, DeviceClinic, UserClinic
from devices.models import Device
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_serializer

User = get_user_model()


@extend_schema_serializer(component_name="WebDevice")
class DeviceSerializer(serializers.ModelSerializer):
    """Serializer básico para Device"""
    origin_display = serializers.CharField(source='get_origin_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'serial', 'origin', 'origin_display', 'model_name', 
            'clickhouse_id', 'sold', 'sold_at', 'is_active', 'created'
        ]


@extend_schema_serializer(component_name="WebGroup")
class GroupSerializer(serializers.ModelSerializer):
    """Serializer básico para Group"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'is_active', 'created', 'modified']


@extend_schema_serializer(component_name="WebClinic")
class ClinicSerializer(serializers.ModelSerializer):
    """Serializer básico para Clinic"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'group', 'group_name', 'address', 
            'phone', 'email', 'device_count', 'is_active', 'created'
        ]
    
    def get_device_count(self, obj):
        """Retorna o número de devices ativos na clínica"""
        return obj.clinic_devices.filter(is_active=True).count()


@extend_schema_serializer(component_name="WebGroupWithClinics")
class GroupWithClinicsSerializer(serializers.ModelSerializer):
    """Serializer para Group com suas clínicas"""
    clinics = ClinicSerializer(many=True, read_only=True)
    clinic_count = serializers.SerializerMethodField()
    total_devices = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'clinic_count', 'total_devices',
            'clinics', 'is_active', 'created', 'modified'
        ]
    
    def get_clinic_count(self, obj):
        """Retorna o número de clínicas ativas no grupo"""
        return obj.clinics.filter(is_active=True).count()
    
    def get_total_devices(self, obj):
        """Retorna o número total de devices em todas as clínicas do grupo"""
        return DeviceClinic.objects.filter(
            clinic__group=obj, 
            clinic__is_active=True,
            is_active=True
        ).count()


@extend_schema_serializer(component_name="WebClinicWithDevices")
class ClinicWithDevicesSerializer(serializers.ModelSerializer):
    """Serializer para Clinic com seus devices"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    devices = serializers.SerializerMethodField()
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'group', 'group_name', 'address', 'phone', 
            'email', 'device_count', 'devices', 'is_active', 'created'
        ]
    
    def get_devices(self, obj):
        """Retorna todos os devices ativos da clínica"""
        device_clinics = obj.clinic_devices.filter(is_active=True).select_related('device')
        devices = [dc.device for dc in device_clinics]
        return DeviceSerializer(devices, many=True).data
    
    def get_device_count(self, obj):
        """Retorna o número de devices ativos na clínica"""
        return obj.clinic_devices.filter(is_active=True).count()


@extend_schema_serializer(component_name="WebDeviceClinic")
class DeviceClinicSerializer(serializers.ModelSerializer):
    """Serializer para DeviceClinic"""
    device = DeviceSerializer(read_only=True)
    clinic = ClinicSerializer(read_only=True)
    
    class Meta:
        model = DeviceClinic
        fields = [
            'id', 'device', 'clinic', 'assigned_at', 
            'notes', 'is_active', 'created', 'modified'
        ]


@extend_schema_serializer(component_name="WebGroupCreate")
class GroupCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de grupos"""
    
    class Meta:
        model = Group
        fields = ['name', 'description']
    
    def validate_name(self, value):
        """Validação customizada para nome único"""
        if Group.objects.filter(name=value, is_active=True).exists():
            raise serializers.ValidationError("Já existe um grupo ativo com este nome.")
        return value
    
    def create(self, validated_data):
        """Cria o grupo e automaticamente adiciona o usuário como admin"""
        from groups.models import GroupAdmin
        
        user = self.context['request'].user
        
        # Criar o grupo
        group = Group.objects.create(**validated_data)
        
        # Automaticamente tornar o criador admin do grupo
        GroupAdmin.objects.create(
            user=user,
            group=group,
            permissions=['full_access']  # Criador tem acesso total
        )
        
        return group