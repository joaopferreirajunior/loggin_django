from rest_framework import serializers
from groups.models import Group, Clinic, DeviceClinic
from devices.api.mobile.v0.serializers import MobileDeviceSerializer
from drf_spectacular.utils import extend_schema_serializer



@extend_schema_serializer(component_name="MobileGroup")
class MobileGroupSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Group mobile"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description']


@extend_schema_serializer(component_name="MobileClinic")
class MobileClinicSerializer(serializers.ModelSerializer):
    """Serializer simplificado para Clinic mobile"""
    groupName = serializers.CharField(source='group.name', read_only=True)
    deviceCount = serializers.SerializerMethodField()
    clinicImageUrl = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'group', 'groupName', 'address', 'phone', 'deviceCount', 'clinicImageUrl']
    
    def validate_name(self, value):
        """Validação do nome da clínica"""
        if not value or not value.strip():
            raise serializers.ValidationError("O nome da clínica não pode estar vazio.")
        return value.strip()
    
    def validate_group(self, value):
        """Validação do grupo"""
        if not value:
            raise serializers.ValidationError("O grupo é obrigatório.")
        if not value.is_active:
            raise serializers.ValidationError("O grupo informado não está ativo.")
        return value
    
    def validate(self, attrs):
        """Validação de duplicidade de nome no grupo"""
        name = attrs.get('name')
        group = attrs.get('group')
        
        # Verifica se já existe uma clínica com este nome neste grupo
        # Exclui a própria clínica se for uma atualização
        queryset = Clinic.objects.filter(name=name, group=group)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError({
                "name": f"Já existe uma clínica com o nome '{name}' neste grupo."
            })
        
        return attrs
    
    def get_deviceCount(self, obj):
        """Retorna o número de devices ativos na clínica"""
        if obj.pk:  # Verifica se o objeto já foi salvo
            return obj.clinic_devices.filter(is_active=True).count()
        return 0
    
    def get_clinicImageUrl(self, obj):
        """Retorna a URL da imagem da clínica"""
        if obj.pk:  # Verifica se o objeto já foi salvo
            return obj.get_clinic_image_url()
        return None


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


@extend_schema_serializer(component_name="MobileGroupCreate")
class MobileGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de grupos mobile"""
    
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


@extend_schema_serializer(component_name="MobileClinicImageUpload")
class MobileClinicImageUploadSerializer(serializers.Serializer):
    """
    Serializer mobile para upload de imagem de clínica
    """
    clinicImage = serializers.ImageField(
        required=True,
        help_text="Imagem da clínica (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_clinicImage(self, value):
        """
        Valida a imagem usando o serviço S3ImageService
        """
        from users.services import S3ImageService
        s3_service = S3ImageService()
        is_valid, error_message = s3_service.validate_image(value)
        
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value
    
    def save(self, clinic):
        """
        Processa e salva a imagem no S3
        """
        try:
            from users.services import S3ImageService
            clinic_image = self.validated_data['clinicImage']
            s3_service = S3ImageService()
            
            # Remove imagem anterior se existir
            if clinic.clinic_image:
                clinic.delete_clinic_image()
            
            # Upload nova imagem
            success, message, s3_key = s3_service.process_and_upload_clinic_image(
                str(clinic.id), clinic_image
            )
            
            if not success:
                raise serializers.ValidationError(f"Erro no upload: {message}")
            
            # Atualiza a clínica com o novo path
            clinic.clinic_image = s3_key
            clinic.save()
            
            return clinic
            
        except serializers.ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log the full error for debugging
            import traceback
            print(f"Erro completo no upload da imagem da clínica: {traceback.format_exc()}")
            raise serializers.ValidationError(f"Erro interno no upload: {str(e)}")