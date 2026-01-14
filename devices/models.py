from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from app.utils import AuditModel  # created, modified, is_active

class Device(AuditModel):
    """Modelo Device com os campos especificados"""
    id = models.AutoField(primary_key=True)
    serial = models.CharField(max_length=22, db_index=True, default="")
    model = models.CharField(max_length=24, db_index=True, default="undefined")
    locked = models.BooleanField(default=False)
    tested = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["serial"]),
            models.Index(fields=["model"]),
            models.Index(fields=["sold"]),
            models.Index(fields=["locked"]),
            models.Index(fields=["tested"]),
            models.Index(fields=["sent"]),
            models.Index(fields=["created"]),
        ]
    
    def __str__(self):
        return f"Device {self.serial or self.id} ({self.model})"
    
    def get_current_clinic(self):
        """Retorna a clínica atual do device (se houver)"""
        current_assignment = self.device_clinics.filter(is_active=True).first()
        return current_assignment.clinic if current_assignment else None
    
    def is_assigned_to_clinic(self):
        """Verifica se o device está atualmente atribuído a uma clínica"""
        return self.device_clinics.filter(is_active=True).exists()
    
    def assign_to_clinic(self, clinic, notes=None):
        """Atribui o device a uma clínica (remove atribuições anteriores)"""
        # Desativa atribuições anteriores
        self.device_clinics.filter(is_active=True).update(is_active=False)
        
        # Cria nova atribuição
        from groups.models import DeviceClinic
        return DeviceClinic.objects.create(
            device=self,
            clinic=clinic,
            notes=notes or "",
            is_active=True
        )
    
    def get_current_telemetry_module(self):
        """Retorna o módulo de telemetria atual do device (se houver)"""
        current_link = self.telemetry_links.filter(is_linked=True).first()
        return current_link.module if current_link else None
    
    def has_telemetry_module(self):
        """Verifica se o device tem um módulo de telemetria vinculado"""
        return self.telemetry_links.filter(is_linked=True).exists()
    
    def link_telemetry_module(self, module):
        """Vincula um módulo de telemetria ao device"""
        # Desvincula módulos anteriores
        self.telemetry_links.filter(is_linked=True).update(
            is_linked=False,
            unlinked_at=timezone.now()
        )
        
        # Desvincula o módulo de outros devices
        module.device_telemetry_links.filter(is_linked=True).update(
            is_linked=False,
            unlinked_at=timezone.now()
        )
        
        # Cria nova vinculação
        from django.utils import timezone
        return DeviceTelemetryModule.objects.create(
            device=self,
            module=module,
            is_linked=True
        )


class TelemetryModule(AuditModel):
    """Módulo de telemetria que pode ser instalado nos devices"""
    id = models.AutoField(primary_key=True)
    imei = models.CharField(
        max_length=16, 
        unique=True,
        db_index=True,
        help_text="Identificador único do módulo de telemetria"
    )
    icc_id = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Identificador ICC do chip SIM"
    )
    modelo = models.CharField(
        max_length=12,
        db_index=True,
        help_text="Modelo do módulo GPS/telemetria"
    )
    last_online_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Última vez que o módulo esteve online"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=["imei"]),
            models.Index(fields=["icc_id"]),
            models.Index(fields=["modelo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["last_online_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['imei'],
                name='unique_telemetry_module_imei'
            )
        ]
    
    def __str__(self):
        return f"TelemetryModule {self.imei} ({self.modelo})"
    
    def get_current_device(self):
        """Retorna o device atual do módulo (se houver)"""
        current_link = self.device_telemetry_links.filter(is_linked=True).first()
        return current_link.device if current_link else None
    
    def is_linked_to_device(self):
        """Verifica se o módulo está atualmente vinculado a um device"""
        return self.device_telemetry_links.filter(is_linked=True).exists()


class DeviceTelemetryModule(models.Model):
    """Relaciona devices com módulos de telemetria"""
    id = models.AutoField(primary_key=True)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="telemetry_links",
        help_text="Device vinculado ao módulo"
    )
    module = models.ForeignKey(
        TelemetryModule,
        on_delete=models.CASCADE,
        related_name="device_telemetry_links",
        help_text="Módulo de telemetria vinculado"
    )
    linked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data de vinculação do módulo ao device"
    )
    unlinked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data de desvinculação (se aplicável)"
    )
    is_linked = models.BooleanField(
        default=True,
        help_text="Se o vínculo está ativo"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=["device", "module"]),
            models.Index(fields=["module", "device"]),
            models.Index(fields=["is_linked"]),
            models.Index(fields=["linked_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'module'],
                condition=models.Q(is_linked=True),
                name='unique_active_device_telemetry_module'
            )
        ]
    
    def __str__(self):
        return f"Device {self.device.serial} ↔ Module {self.module.imei}"
    
    def unlink(self):
        """Desvincula o módulo do device"""
        from django.utils import timezone
        self.is_linked = False
        self.unlinked_at = timezone.now()
        self.save()
    
class DeviceLocation(models.Model):
    device   = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="locations",
        null=True,
        blank=True,
        help_text="Device que possui esta localização"
    )
    module = models.ForeignKey(
        TelemetryModule,
        on_delete=models.SET_NULL,
        related_name="locations",
        null=True,
        blank=True,
        help_text="Módulo de telemetria que enviou esta localização"
    )
    read_at  = models.DateTimeField(db_index=True)
    # 6 casas decimais ≈ ~0,11 m — suficiente para limiar de 100 m
    latitude  = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        # consultas do tipo: WHERE device = ? ORDER BY read_at DESC LIMIT 1
        ordering = ["device", "-read_at"]
        indexes = [
            models.Index(fields=["device", "-read_at"], name="idx_devloc_dev_readat_desc"),
            models.Index(fields=["module", "-read_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="latitude_range",
                check=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
            ),
            models.CheckConstraint(
                name="longitude_range",
                check=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
            ),
        ]

    def __str__(self):
        return f"{self.device_id} @ {self.latitude},{self.longitude} ({self.read_at:%Y-%m-%d %H:%M:%S})"
    
class DeviceNfeHistory(AuditModel):
    device   = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="nfe_history",
    )
    nfe      = models.CharField(max_length=255)                 # número/chave da NFe
    nfe_date = models.DateTimeField()                           
    cfop     = models.PositiveIntegerField(null=True, blank=True)
    ciof     = models.PositiveIntegerField(null=True, blank=True)
    source   = models.CharField(max_length=64, default="Tecnicon")

    class Meta:
        # Ordena naturalmente pela mais recente dentro do device
        ordering = ["device", "-nfe_date"]
        indexes = [
            # consultas mais comuns: “mais recente por device”
            models.Index(fields=["device", "nfe_date"]),
            models.Index(fields=["device", "-nfe_date"], name="idx_dev_nfe_desc"),
            models.Index(fields=["nfe"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Device NFe history"
        verbose_name_plural = "Device NFe histories"

    def __str__(self):
        return f"{self.device_id} · {self.nfe} · {self.nfe_date:%Y-%m-%d}"


class DeviceEvent(models.Model):
    """Registra eventos de auditoria de devices"""
    EVENT_CHOICES = [
        ('sold', 'Sold'),
        ('sent', 'Sent'),
        ('tested', 'Tested'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
    ]
    
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="events",
        help_text="Device relacionado ao evento"
    )
    event = models.CharField(
        max_length=20,
        choices=EVENT_CHOICES,
        db_index=True,
        help_text="Tipo de evento: sold, sent, tested, locked, unlocked"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Data e hora da ocorrência do evento"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="device_events",
        help_text="Usuário que criou o evento"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['event', '-created_at']),
            models.Index(fields=['device', 'event', '-created_at']),
        ]
        verbose_name = "Device Event"
        verbose_name_plural = "Device Events"
    
    def __str__(self):
        return f"{self.device.serial} - {self.event} ({self.created_at:%Y-%m-%d %H:%M:%S})"


@receiver(post_save, sender=DeviceEvent)
def update_device_status(sender, instance, created, **kwargs):
    """Atualiza o status do device quando um evento é criado"""
    if created:
        device = instance.device
        event_type = instance.event
        
        if event_type == 'sold':
            device.sold = True
        elif event_type == 'sent':
            device.sent = True
        elif event_type == 'tested':
            device.tested = True
        elif event_type == 'locked':
            device.locked = True
        elif event_type == 'unlocked':
            device.locked = False
        
        device.save(update_fields=['sold', 'sent', 'tested', 'locked'])
    
# Mais recente de um device (eficiente com o índice composto)
#latest = DeviceNfeHistory.objects.filter(device=dev).order_by("-nfe_date").first()