from django.db import models
from app.utils import AuditModel  # created, modified, is_active

class DeviceOrigin(models.IntegerChoices):
    MEDIO     = 1, "MedIO"
    MICROFLOW = 2, "MicroFlow"
    NEXOUWB   = 3, "NexoUWB"

class Device(AuditModel):
    serial = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    origin = models.PositiveSmallIntegerField(choices=DeviceOrigin.choices, default=DeviceOrigin.MEDIO)
    iccid = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    model_name = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    sold = models.BooleanField(null=True, blank=True, db_index=True)
    sold_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
    lock = models.BooleanField(null=True, blank=True, db_index=True)
    lock_at = models.DateTimeField(null=True, blank=True, db_index=True)
    tested = models.BooleanField(null=True, blank=True, db_index=True)
    tested_at = models.DateTimeField(null=True, blank=True, db_index=True)
    clickhouse_id = models.CharField(max_length=255, unique=True, db_index=True)
    # resto "cauda longa"
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["origin"]),
            models.Index(fields=["serial"]),
            models.Index(fields=["iccid"]),
            models.Index(fields=["model_name"]),
            models.Index(fields=["sold", "sold_at"]),  # composto útil p/ relatórios
        ]
    
    def __str__(self):
        return f"Device {self.serial or self.id} ({self.get_origin_display()})"
    
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
        return DeviceClinic.objects.create(
            device=self,
            clinic=clinic,
            notes=notes or "",
            is_active=True
        )
    
class DeviceLocation(models.Model):
    device   = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="locations",
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
    
# Mais recente de um device (eficiente com o índice composto)
#latest = DeviceNfeHistory.objects.filter(device=dev).order_by("-nfe_date").first()