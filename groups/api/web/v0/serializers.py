from rest_framework import serializers
from groups.models import Group, Clinic, DeviceClinic, UserClinic
from devices.models import Device
from django.contrib.auth import get_user_model

User = get_user_model()


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer básico para Device"""
    origin_display = serializers.CharField(source='get_origin_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'serial', 'origin', 'origin_display', 'model_name', 
            'clickhouse_id', 'sold', 'sold_at', 'is_active', 'created'
        ]


class GroupSerializer(serializers.ModelSerializer):
    """Serializer básico para Group"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'is_active', 'created', 'modified']


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