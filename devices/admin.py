from django.contrib import admin
from .models import (
    Device, DeviceLocation, DeviceNfeHistory, TelemetryModule, 
    DeviceTelemetryModule, DeviceEvent, DeviceModel, DeviceFeatures, DeviceLease
)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial', 'device_model', 'name', 'sold', 'sent', 'tested', 'locked', 'is_active', 'created')
    list_filter = ('device_model', 'sold', 'sent', 'tested', 'locked', 'is_active', 'created')
    search_fields = ('serial', 'name', 'device_model__name', 'token', 'lease__lease_id')
    ordering = ('-created',)
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('device_model', 'lease')
    
    fieldsets = (
        (None, {
            'fields': ('serial', 'device_model', 'name', 'description')
        }),
        ('Authentication', {
            'fields': ('token', 'secret'),
            'classes': ('collapse',)
        }),
        ('Lease Information', {
            'fields': ('lease',),
            'classes': ('collapse',)
        }),
        ('Ratings', {
            'fields': ('rating_delivery', 'rating_buy'),
            'classes': ('collapse',)
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


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created')
    list_filter = ('is_active', 'created')
    search_fields = ('name', 'slug', 'description')
    ordering = ('name',)
    readonly_fields = ('created', 'modified')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Media', {
            'fields': ('icon_url',),
            'description': 'Path do ícone no S3 (ex: device-models/slug/icon.png)'
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceFeatures)
class DeviceFeaturesAdmin(admin.ModelAdmin):
    list_display = ('title', 'device_model', 'kind', 'order', 'is_active', 'created')
    list_filter = ('device_model', 'kind', 'is_active', 'created')
    search_fields = ('title', 'description', 'device_model__name')
    ordering = ('device_model', 'order', 'title')
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('device_model',)
    
    fieldsets = (
        (None, {
            'fields': ('device_model', 'title', 'description', 'kind', 'icon', 'order')
        }),
        ('File', {
            'fields': ('file_url',),
            'description': 'Path do arquivo no S3 (ex: device-features/feature_id/manual.pdf)'
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceLease)
class DeviceLeaseAdmin(admin.ModelAdmin):
    list_display = ('lease_id', 'device', 'user', 'start_date', 'end_date', 'rating_delivery', 'rating_buy', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('lease_id', 'device__serial', 'user__email', 'user__username')
    ordering = ('-start_date',)
    readonly_fields = ('lease_id', 'created', 'modified')
    raw_id_fields = ('device', 'user')
    
    fieldsets = (
        (None, {
            'fields': ('lease_id', 'device', 'user')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Ratings', {
            'fields': ('rating_delivery', 'rating_buy'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('is_active', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )
