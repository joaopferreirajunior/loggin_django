from django.contrib import admin
from .models import Group, Clinic, GroupAdmin as GroupAdminModel, DeviceClinic, UserClinic


@admin.register(Group)
class GroupModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created', 'modified')
    list_filter = ('is_active', 'created', 'modified')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('id', 'created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'phone', 'email', 'is_active', 'created')
    list_filter = ('group', 'is_active', 'created', 'modified')
    search_fields = ('name', 'address', 'phone', 'email')
    ordering = ('group__name', 'name')
    readonly_fields = ('id', 'created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'group')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupAdminModel)
class GroupAdminModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'is_active', 'created')
    list_filter = ('group', 'is_active', 'created', 'modified')
    search_fields = ('user__username', 'user__email', 'group__name')
    ordering = ('group__name', 'user__username')
    readonly_fields = ('id', 'created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'group')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceClinic)
class DeviceClinicAdmin(admin.ModelAdmin):
    list_display = ('device', 'clinic', 'assigned_at', 'is_active', 'created')
    list_filter = ('clinic__group', 'is_active', 'assigned_at', 'created')
    search_fields = ('device__serial', 'clinic__name', 'clinic__group__name', 'notes')
    ordering = ('-assigned_at',)
    raw_id_fields = ('device', 'clinic')
    readonly_fields = ('id', 'assigned_at', 'created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('device', 'clinic')
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'assigned_at', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserClinic)
class UserClinicAdmin(admin.ModelAdmin):
    list_display = ('user', 'clinic', 'role', 'is_active', 'start_date', 'end_date')
    list_filter = ('clinic__group', 'clinic', 'is_active', 'start_date')
    search_fields = ('user__username', 'user__email', 'clinic__name', 'role')
    ordering = ('-start_date',)
    readonly_fields = ('id', 'start_date', 'created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'clinic', 'role')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )
