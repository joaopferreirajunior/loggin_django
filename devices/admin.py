from django.contrib import admin
from .models import Device, DeviceLocation, DeviceNfeHistory


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial', 'origin', 'model_name', 'sold', 'sold_at', 'is_active', 'created')
    list_filter = ('origin', 'sold', 'tested', 'is_active', 'created')
    search_fields = ('serial', 'iccid', 'model_name', 'clickhouse_id')
    ordering = ('-created',)
    readonly_fields = ('created', 'modified')
    
    fieldsets = (
        (None, {
            'fields': ('serial', 'origin', 'model_name', 'clickhouse_id')
        }),
        ('Status', {
            'fields': ('sold', 'sold_at', 'sent_at', 'tested', 'tested_at', 'lock', 'lock_at')
        }),
        ('Technical', {
            'fields': ('iccid', 'metadata')
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceLocation)
class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = ('device', 'latitude', 'longitude', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('device__serial', 'device__clickhouse_id')
    ordering = ('-read_at',)
    raw_id_fields = ('device',)


@admin.register(DeviceNfeHistory)
class DeviceNfeHistoryAdmin(admin.ModelAdmin):
    list_display = ('device', 'nfe', 'nfe_date', 'cfop', 'source', 'is_active')
    list_filter = ('source', 'is_active', 'nfe_date')
    search_fields = ('device__serial', 'nfe', 'device__clickhouse_id')
    ordering = ('-nfe_date',)
    raw_id_fields = ('device',)
    readonly_fields = ('created', 'modified')
