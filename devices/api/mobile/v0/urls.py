from django.urls import path
from . import views

urlpatterns = [
    # Device endpoints (mobile format with camelCase)
    path('devices/', views.MobileDeviceCreateView.as_view(), name='mobile_device_create'),
    path('devices/<uuid:deviceId>/', views.MobileDeviceDetailView.as_view(), name='mobile_device_detail'),
    path('devices/<uuid:deviceId>/tested/', views.MobileDeviceTestView.as_view(), name='mobile_device_test'),
    path('devices/<uuid:deviceId>/sold/', views.MobileDeviceSoldView.as_view(), name='mobile_device_sell'),
    
    # Device Location endpoints (mobile)
    path('devices/locations/', views.MobileDeviceLocationCreateView.as_view(), name='mobile_device_location_create'),
    path('devices/locations/global/', views.MobileDeviceGlobalLocationsView.as_view(), name='mobile_device_global_locations'),
    
    # Telemetry Module endpoints (mobile)
    path('modules/', views.MobileTelemetryModuleCreateView.as_view(), name='mobile_telemetry_module_create'),
    path('modules/<uuid:moduleId>/', views.MobileTelemetryModuleDetailView.as_view(), name='mobile_telemetry_module_detail'),
    
    # Device-Telemetry Module relationship endpoints (mobile)
    path('devices/link-module/', views.MobileDeviceTelemetryModuleLinkView.as_view(), name='mobile_device_telemetry_link'),
]