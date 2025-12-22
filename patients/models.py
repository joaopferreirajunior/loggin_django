import uuid
from django.db import models


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamento com grupo (obrigatório)
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.PROTECT,
        related_name='patients',
        help_text="Grupo ao qual o paciente pertence"
    )

    full_name = models.CharField(max_length=255)
    photo = models.URLField(null=True, blank=True)  # ou CharField se não for URL fixa
    birth_date = models.DateField()

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        UNKNOWN = "UNKNOWN", "Unknown"

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
    )

    cpf = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    full_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)  # mapeia createdAt
    updated_at = models.DateTimeField(auto_now=True)      # mapeia updatedAt

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name
    
    def get_patient_photo_url(self):
        """Retorna URL presigned da foto do paciente se existir"""
        if not self.photo:
            return None
        
        from users.services import S3ImageService
        s3_service = S3ImageService()
        return s3_service.generate_presigned_url(self.photo)
    
    def delete_patient_photo(self):
        """Remove a foto do paciente do S3"""
        if not self.photo:
            return False
        
        try:
            from users.services import S3ImageService
            s3_service = S3ImageService()
            s3_service.delete_image(self.photo)
            self.photo = None
            self.save()
            return True
        except Exception as e:
            print(f"Erro ao deletar foto do paciente {self.id}: {e}")
            return False
    
    def get_my_doctors(self, active_only=True):
        """Retorna todos os usuários que atendem este paciente"""
        from users.models import UserPatientRelation
        return UserPatientRelation.get_patient_users(self, active_only)
    
    def get_doctor_count(self, active_only=True):
        """Retorna o número de usuários que atendem este paciente"""
        return self.get_my_doctors(active_only).count()
    
    def is_treated_by_user(self, user):
        """Verifica se este paciente está sendo atendido por um usuário específico"""
        from users.models import UserPatientRelation
        return UserPatientRelation.objects.filter(
            user=user,
            patient=self,
            is_active=True
        ).exists()
    
    def add_doctor(self, user, notes=None):
        """Adiciona um usuário aos cuidadores deste paciente"""
        from users.models import UserPatientRelation
        return UserPatientRelation.create_relation(
            user=user,
            patient=self,
            notes=notes
        )


class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medical_records",
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="medical_records",
        help_text="Doutor que criou o prontuário"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    complaint = models.TextField()
    clinical_notes = models.TextField()

    def __str__(self):
        return f"{self.patient.full_name} - {self.created_at:%Y-%m-%d}"


class Anamnesis(models.Model):
    """Modelo para armazenar anamneses dos pacientes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patients = models.ManyToManyField(
        Patient,
        related_name="anamneses",
        help_text="Pacientes associados a esta anamnese"
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="anamneses",
        help_text="Médico que criou a anamnese"
    )

    metadata = models.TextField(help_text="Dados da anamnese em formato de texto/JSON")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Anamnesis"
        verbose_name_plural = "Anamneses"
        ordering = ['-created_at']

    def __str__(self):
        patient_names = ", ".join([p.full_name for p in self.patients.all()[:3]])
        return f"Anamnesis - {patient_names} - {self.created_at:%Y-%m-%d}"
