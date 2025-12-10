from rest_framework import serializers
from groups.models import Group, Clinic, DeviceClinic
from devices.models import Device
from drf_spectacular.utils import extend_schema_serializer


@extend_schema_serializer(component_name="MobileDevice")
class MobileDeviceSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Device mobile"""
    origin_display = serializers.CharField(source='get_origin_display', read_only=True)
    
    class Meta:
        model = Device
        fields = ['id', 'serial', 'origin', 'origin_display', 'model_name', 'sold', 'is_active']


@extend_schema_serializer(component_name="MobileGroup")
class MobileGroupSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Group mobile"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description']


@extend_schema_serializer(component_name="MobileClinic")
class MobileClinicSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Clinic mobile"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'group_name', 'address', 'phone', 'device_count']
    
    def get_device_count(self, obj):
        """Retorna o número de devices ativos na clínica"""
        return obj.clinic_devices.filter(is_active=True).count()


@extend_schema_serializer(component_name="MobileGroupWithClinics")
class MobileGroupWithClinicsSerializer(serializers.ModelSerializer):
    """Serializer para Group com suas clínicas mobile"""
    clinics = MobileClinicSerializer(many=True, read_only=True)
    clinic_count = serializers.SerializerMethodField()
    total_devices = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'clinic_count', 'total_devices', 'clinics']
    
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


@extend_schema_serializer(component_name="MobileClinicWithDevices")
class MobileClinicWithDevicesSerializer(serializers.ModelSerializer):
    """Serializer para Clinic com seus devices mobile"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    devices = serializers.SerializerMethodField()
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'group_name', 'device_count', 'devices']
    
    def get_devices(self, obj):
        """Retorna todos os devices ativos da clínica"""
        device_clinics = obj.clinic_devices.filter(is_active=True).select_related('device')
        devices = [dc.device for dc in device_clinics]
        return MobileDeviceSerializer(devices, many=True).data
    
    def get_device_count(self, obj):
        """Retorna o número de devices ativos na clínica"""
        return obj.clinic_devices.filter(is_active=True).count()


@extend_schema_serializer(component_name="MobileDetailResponse")
class MobileDetailResponseSerializer(serializers.Serializer):
    """Resposta padrão com mensagem de detail"""
    detail = serializers.CharField()