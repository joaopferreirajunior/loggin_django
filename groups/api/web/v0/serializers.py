from rest_framework import serializers
from groups.models import Group, Clinic, DeviceClinic, UserClinic
from devices.api.web.v0.serializers import DeviceSerializer
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_serializer
from drf_spectacular.openapi import OpenApiExample

User = get_user_model()


@extend_schema_serializer(component_name="WebGroup")
class GroupSerializer(serializers.ModelSerializer):
    """Serializer básico para Group"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'is_active', 'created', 'modified']


@extend_schema_serializer(component_name="WebClinic")
class ClinicSerializer(serializers.ModelSerializer):
    """Serializer básico para Clinic"""
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    clinic_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'group', 'group_name', 
            # ClinicData - obrigatórios
            'cpf_cnpj', 'trade_name', 'phone', 'email',
            # Address - opcionais
            'country', 'zip_code', 'street', 'number', 'district', 
            'city', 'state', 'time_zone',
            # BankData - opcionais
            'bank_code', 'branch', 'branch_digit', 'account_number', 
            'account_digit', 'account_type',
            # Outros
            'device_count', 'clinic_image_url', 'is_active', 'created'
        ]
    
    def validate_name(self, value):
        """Validação do nome da clínica"""
        if not value or not value.strip():
            raise serializers.ValidationError("O nome da clínica não pode estar vazio.")
        return value.strip()
    
    def validate_cpf_cnpj(self, value):
        """Validação do CPF/CNPJ"""
        if not value or not value.strip():
            raise serializers.ValidationError("O CPF/CNPJ é obrigatório.")
        return value.strip()
    
    def validate_trade_name(self, value):
        """Validação do nome fantasia"""
        if not value or not value.strip():
            raise serializers.ValidationError("O nome fantasia é obrigatório.")
        return value.strip()
    
    def validate_phone(self, value):
        """Validação do telefone"""
        if not value or not value.strip():
            raise serializers.ValidationError("O telefone é obrigatório.")
        return value.strip()
    
    def validate_email(self, value):
        """Validação do email"""
        if not value or not value.strip():
            raise serializers.ValidationError("O email é obrigatório.")
        return value.strip().lower()
    
    def get_device_count(self, obj):
        """Retorna o número de devices ativos na clínica"""
        if obj.pk:  # Verifica se o objeto já foi salvo
            return obj.clinic_devices.filter(is_active=True).count()
        return 0
    
    def get_clinic_image_url(self, obj):
        """Retorna a URL da imagem da clínica"""
        if obj.pk:  # Verifica se o objeto já foi salvo
            return obj.get_clinic_image_url()
        return None



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


@extend_schema_serializer(
    component_name="WebClinicImageUpload",
    examples=[
        OpenApiExample(
            "Upload de Imagem da Clínica",
            summary="Exemplo de upload de imagem",
            description="Upload de imagem de uma clínica",
            value={
                "clinic_image": "binary_image_data"
            }
        )
    ]
)
class ClinicImageUploadSerializer(serializers.Serializer):
    """
    Serializer para upload de imagem de clínica
    """
    clinic_image = serializers.ImageField(
        required=True,
        help_text="Imagem da clínica (JPEG, PNG, WebP - máximo 5MB)"
    )
    
    def validate_clinic_image(self, value):
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
            clinic_image = self.validated_data['clinic_image']
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