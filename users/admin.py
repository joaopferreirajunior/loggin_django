from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import Profile, UserPatientRelation, Role

User = get_user_model()


# Customizar o nome de exibição do modelo Group (roles)
class RoleAdmin(admin.ModelAdmin):
    """Admin customizado para roles (Django Groups)"""
    list_display = ('name', 'permission_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Número de Permissões'


# Desregistrar o admin padrão de Group e registrar o customizado com modelo proxy
admin.site.unregister(Group)
admin.site.register(Role, RoleAdmin)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = "user"

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# troca o admin padrão para incluir o inline
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "cpf", "birth", "phone")
    search_fields = ("user__username", "user__email", "cpf", "phone")


@admin.register(UserPatientRelation)
class UserPatientRelationAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'patient_display',
        'is_active', 'start_date', 'end_date'
    )
    list_filter = ('is_active', 'start_date', 'created')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'patient__full_name', 'patient__cpf'
    )
    ordering = ('-start_date',)
    readonly_fields = ('id', 'created', 'modified')
    
    fieldsets = (
        ('Relacionamento', {
            'fields': ('user', 'patient')
        }),
        ('Status', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ('Observações', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('id', 'created', 'modified'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username}"
    user_display.short_description = 'Usuário'
    
    def patient_display(self, obj):
        return obj.patient.full_name
    patient_display.short_description = 'Paciente'
    
    actions = ['deactivate_relations', 'activate_relations']
    
    def deactivate_relations(self, request, queryset):
        count = 0
        for relation in queryset:
            if relation.is_active:
                relation.deactivate()
                count += 1
        self.message_user(request, f"{count} relacionamento(s) desativado(s) com sucesso.")
    deactivate_relations.short_description = "Desativar relacionamentos selecionados"
    
    def activate_relations(self, request, queryset):
        count = 0
        for relation in queryset:
            if not relation.is_active:
                relation.activate()
                count += 1
        self.message_user(request, f"{count} relacionamento(s) ativado(s) com sucesso.")
    activate_relations.short_description = "Ativar relacionamentos selecionados"
