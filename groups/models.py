from django.db import models
from django.conf import settings
from app.utils import AuditModel
import uuid


class Group(AuditModel):
    """
    Representa um grupo de clínicas.
    Cada grupo pode ter múltiplas clínicas e administradores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Nome do grupo de clínicas"
    )
    description = models.TextField(
        blank=True,
        help_text="Descrição opcional do grupo"
    )
    
    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Clinic(AuditModel):
    """
    Representa uma clínica que pertence a um grupo.
    Cada clínica só pode pertencer a um grupo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        help_text="Nome da clínica"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="clinics",
        help_text="Grupo ao qual a clínica pertence"
    )
    
    # ClinicData - Campos obrigatórios da clínica
    cpf_cnpj = models.CharField(
        max_length=20,
        default="",
        help_text="CPF ou CNPJ da clínica"
    )
    trade_name = models.CharField(
        default="",
        max_length=255,
        help_text="Nome fantasia da clínica"
    )
    phone = models.CharField(
        default="",
        max_length=20,
        help_text="Telefone da clínica"
    )
    email = models.EmailField(
        default="",
        help_text="Email da clínica"
    )
    
    # Address - Campos opcionais de endereço
    country = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Código do país (ex: BR)"
    )
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="CEP"
    )
    street = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Rua/Avenida"
    )
    number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Bairro"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Cidade"
    )
    state = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Estado (sigla)"
    )
    time_zone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='America/Sao_Paulo',
        help_text="Fuso horário (ex: America/Sao_Paulo)"
    )
    
    # BankData - Campos opcionais de dados bancários
    bank_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Código do banco (ex: 001 para Banco do Brasil)"
    )
    branch = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Agência bancária"
    )
    branch_digit = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Dígito verificador da agência"
    )
    account_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número da conta bancária"
    )
    account_digit = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Dígito verificador da conta"
    )
    
    class AccountType(models.TextChoices):
        CHECKING = "CHECKING", "Conta Corrente"
        SAVINGS = "SAVINGS", "Conta Poupança"
    
    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
        blank=True,
        null=True,
        help_text="Tipo da conta bancária"
    )
    
    # Imagem da clínica - armazena apenas o path/key do S3
    clinic_image = models.CharField(
        max_length=500, 
        null=True, 
        blank=True,
        help_text="Path da imagem da clínica no bucket S3 (ex: clinics/clinic_123/image.jpg)"
    )
    
    class Meta:
        verbose_name = "Clinic"
        verbose_name_plural = "Clinics"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['group']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'group'],
                name='unique_clinic_name_per_group'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.group.name})"
    
    def get_active_devices(self):
        """Retorna todos os devices ativos atribuídos a esta clínica"""
        return [dc.device for dc in self.clinic_devices.filter(is_active=True).select_related('device')]
    
    def get_device_count(self):
        """Retorna o número de devices ativos na clínica"""
        return self.clinic_devices.filter(is_active=True).count()
    
    def has_device(self, device):
        """Verifica se um device específico está atribuído a esta clínica"""
        return self.clinic_devices.filter(device=device, is_active=True).exists()
    
    def get_clinic_image_url(self) -> str:
        """Retorna URL assinada temporária da imagem da clínica do S3"""
        if self.clinic_image:
            try:
                from users.services import S3ImageService
                s3_service = S3ImageService()
                presigned_url = s3_service.generate_presigned_url(self.clinic_image)
                return presigned_url
            except Exception as e:
                print(f"Erro ao gerar presigned URL para clínica: {e}")
                return None
        return None
    
    def delete_clinic_image(self):
        """Remove a imagem do S3 e limpa o campo no banco"""
        if self.clinic_image:
            try:
                import boto3
                from django.conf import settings
                
                # Usa IAM Role da instância EC2 automaticamente
                s3_client = boto3.client(
                    's3',
                    region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
                )
                
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'medicalsan-uploads')
                s3_client.delete_object(Bucket=bucket_name, Key=self.clinic_image)
                
                self.clinic_image = None
                self.save()
                return True
            except Exception as e:
                print(f"Erro ao deletar imagem da clínica do S3: {e}")
                return False
        return True


class GroupAdmin(AuditModel):
    """
    Relaciona usuários (auth_user) como administradores de grupos.
    Um usuário pode administrar múltiplos grupos e um grupo pode ter múltiplos administradores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_admins",
        help_text="Usuário administrador do grupo"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="group_admins",
        help_text="Grupo administrado pelo usuário"
    )
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="Permissões específicas do admin neste grupo"
    )
    
    class Meta:
        verbose_name = "Group Admin"
        verbose_name_plural = "Group Admins"
        indexes = [
            models.Index(fields=['user', 'group']),
            models.Index(fields=['group', 'user']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'group'],
                name='unique_user_group_admin'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - Admin of {self.group.name}"


class DeviceClinic(AuditModel):
    """
    Relaciona um device a uma clínica.
    Nem todo device pertence a uma clínica (pode estar em fábrica, dealers, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="device_clinics",
        help_text="Device associado à clínica"
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="clinic_devices",
        help_text="Clínica onde o device está instalado"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de atribuição do device à clínica"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notas sobre a instalação/atribuição"
    )
    
    class Meta:
        verbose_name = "Device Clinic"
        verbose_name_plural = "Device Clinics"
        indexes = [
            models.Index(fields=['device', 'clinic']),
            models.Index(fields=['clinic', 'device']),
            models.Index(fields=['assigned_at']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'clinic'],
                condition=models.Q(is_active=True),
                name='unique_active_device_clinic'
            )
        ]
    
    def __str__(self):
        return f"{self.device.serial or self.device.id} @ {self.clinic.name}"


class UserClinic(AuditModel):
    """
    Relaciona usuários a clínicas.
    Define em quais clínicas um usuário (médico, enfermeiro, etc.) trabalha.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_clinics",
        help_text="Usuário vinculado à clínica"
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="clinic_users",
        help_text="Clínica onde o usuário trabalha"
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        help_text="Função do usuário na clínica (médico, enfermeiro, etc.)"
    )
    start_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de início do vínculo"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data de fim do vínculo (se aplicável)"
    )
    
    class Meta:
        verbose_name = "User Clinic"
        verbose_name_plural = "User Clinics"
        indexes = [
            models.Index(fields=['user', 'clinic']),
            models.Index(fields=['clinic', 'user']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'clinic'],
                name='unique_user_clinic'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} @ {self.clinic.name}"
