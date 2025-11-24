from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile

User = get_user_model()

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
