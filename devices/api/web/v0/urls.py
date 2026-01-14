from django.urls import path
from . import views

urlpatterns = [
    # Device endpoints
    path('devices/', views.DeviceCreateView.as_view(), name='device_create'),
    path('devices/<uuid:device_id>/', views.DeviceDetailView.as_view(), name='device_detail'),
    path('devices/<uuid:device_id>/events/', views.DeviceEventCreateView.as_view(), name='device_event_create'),
    path('devices/<uuid:device_id>/events/list/', views.DeviceEventListView.as_view(), name='device_event_list'),
    
    # Device Location endpoints
    path('devices/locations/', views.DeviceLocationCreateView.as_view(), name='device_location_create'),
    path('devices/locations/global/', views.DeviceGlobalLocationsView.as_view(), name='device_global_locations'),
    path('devices/locations/<uuid:device_id>/', views.DeviceLocationsListView.as_view(), name='device_locations_list'),
    
    # Telemetry Module endpoints
    path('modules/', views.TelemetryModuleCreateView.as_view(), name='telemetry_module_create'),
    path('modules/<uuid:module_id>/', views.TelemetryModuleDetailView.as_view(), name='telemetry_module_detail'),
    
    # Device-Telemetry Module relationship endpoints
    path('devices/link-module/', views.DeviceTelemetryModuleLinkView.as_view(), name='device_telemetry_link'),
]