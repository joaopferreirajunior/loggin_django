from django.contrib import admin
from .models import Device, DeviceLocation, DeviceNfeHistory, TelemetryModule, DeviceTelemetryModule, DeviceEvent


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial', 'model', 'sold', 'sent', 'tested', 'locked', 'is_active', 'created')
    list_filter = ('model', 'sold', 'sent', 'tested', 'locked', 'is_active', 'created')
    search_fields = ('serial', 'model')
    ordering = ('-created',)
    readonly_fields = ('created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('serial', 'model')
        }),
        ('Status', {
            'fields': ('sold', 'sent', 'tested', 'locked')
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceEvent)
class DeviceEventAdmin(admin.ModelAdmin):
    list_display = ('device', 'event', 'user', 'created_at')
    list_filter = ('event', 'created_at')
    search_fields = ('device__serial', 'user__email', 'user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    raw_id_fields = ('device', 'user')
    
    fieldsets = (
        (None, {
            'fields': ('device', 'event', 'user')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )



@admin.register(DeviceLocation)
class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = ('device', 'latitude', 'longitude', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('device__serial',)
    ordering = ('-read_at',)
    raw_id_fields = ('device',)


@admin.register(DeviceNfeHistory)
class DeviceNfeHistoryAdmin(admin.ModelAdmin):
    list_display = ('device', 'nfe', 'nfe_date', 'cfop', 'source', 'is_active')
    list_filter = ('source', 'is_active', 'nfe_date')
    search_fields = ('device__serial', 'nfe')
    ordering = ('-nfe_date',)
    raw_id_fields = ('device',)
    readonly_fields = ('created', 'modified')


@admin.register(TelemetryModule)
class TelemetryModuleAdmin(admin.ModelAdmin):
    list_display = ('imei', 'icc_id', 'modelo', 'is_active', 'created')
    list_filter = ('modelo', 'is_active', 'created')
    search_fields = ('imei', 'icc_id', 'modelo')
    ordering = ('-created',)
    readonly_fields = ('created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('imei', 'icc_id', 'modelo')
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceTelemetryModule)
class DeviceTelemetryModuleAdmin(admin.ModelAdmin):
    list_display = ('device', 'module', 'linked_at', 'unlinked_at', 'is_linked')
    list_filter = ('is_linked', 'linked_at', 'unlinked_at')
    search_fields = ('device__serial', 'module__imei', 'module__icc_id')
    ordering = ('-linked_at',)
    raw_id_fields = ('device', 'module')
    readonly_fields = ('linked_at', 'unlinked_at')
