from django.contrib import admin
from .models import Patient, MedicalRecord


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'cpf', 'birth_date', 'gender', 'city', 'is_active', 'created_at')
    list_filter = ('gender', 'is_active', 'city', 'region', 'created_at')
    search_fields = ('full_name', 'cpf', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('full_name', 'photo', 'birth_date', 'gender')
        }),
        ('Contato', {
            'fields': ('cpf', 'phone', 'email')
        }),
        ('Endereço', {
            'fields': ('full_address', 'city', 'region', 'cep')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor_name', 'created_at', 'complaint_preview')
    list_filter = ('created_at', 'doctor_name')
    search_fields = ('patient__full_name', 'doctor_name', 'complaint')
    ordering = ('-created_at',)
    readonly_fields = ('id',)
    
    def complaint_preview(self, obj):
        return obj.complaint[:50] + '...' if len(obj.complaint) > 50 else obj.complaint
    complaint_preview.short_description = 'Queixa (Preview)'
    
    fieldsets = (
        ('Informações do Atendimento', {
            'fields': ('patient', 'doctor_name', 'created_at')
        }),
        ('Dados Clínicos', {
            'fields': ('complaint', 'clinical_notes')
        }),
        ('Anamnese', {
            'fields': ('anamnese',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )
