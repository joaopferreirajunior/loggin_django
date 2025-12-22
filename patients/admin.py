from django.contrib import admin
from .models import Patient, MedicalRecord, Anamnesis


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'cpf', 'birth_date', 'gender', 'city', 'is_active', 'created_at')
    list_filter = ('gender', 'is_active', 'city', 'region', 'created_at', 'group')
    search_fields = ('full_name', 'cpf', 'email', 'phone', 'group__name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Grupo', {
            'fields': ('group',)
        }),
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
    list_display = ('patient', 'user', 'created_at', 'complaint_preview')
    list_filter = ('created_at',)
    search_fields = ('patient__full_name', 'user__first_name', 'user__last_name', 'complaint')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')
    
    def complaint_preview(self, obj):
        return obj.complaint[:50] + '...' if len(obj.complaint) > 50 else obj.complaint
    complaint_preview.short_description = 'Queixa (Preview)'
    
    fieldsets = (
        ('Informações do Atendimento', {
            'fields': ('patient', 'user', 'created_at')
        }),
        ('Dados Clínicos', {
            'fields': ('complaint', 'clinical_notes')
        }),
        ('Metadados', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )


@admin.register(Anamnesis)
class AnamnesisAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patients', 'user', 'created_at', 'modified_at')
    list_filter = ('created_at', 'modified_at')
    search_fields = ('patients__full_name', 'user__first_name', 'user__last_name', 'metadata')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'modified_at')
    filter_horizontal = ('patients',)
    
    def get_patients(self, obj):
        return ", ".join([p.full_name for p in obj.patients.all()[:3]])
    get_patients.short_description = 'Pacientes'
    
    fieldsets = (
        ('Informações da Anamnese', {
            'fields': ('user', 'patients')
        }),
        ('Dados', {
            'fields': ('metadata',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )
