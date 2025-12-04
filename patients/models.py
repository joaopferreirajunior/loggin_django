import uuid
from django.db import models


class Patient(models.Model):
    # No Dart o id é String; aqui vou usar UUID, mas você pode trocar
    # por CharField se quiser manter totalmente livre.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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

    created_at = models.DateTimeField()  # vem do createdAt do front
    doctor_name = models.CharField(max_length=255)
    complaint = models.TextField()
    clinical_notes = models.TextField()

    # Não temos o modelo de Anamnese -> JSON genérico
    anamnese = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.created_at:%Y-%m-%d}"
