from django.urls import path
from . import views

urlpatterns = [
    # Device endpoints
    path('devices/create/', views.DeviceCreateView.as_view(), name='device_create'),
    path('devices/<uuid:device_id>/tested/', views.DeviceTestView.as_view(), name='device_test'),
    path('devices/<uuid:device_id>/sold/', views.DeviceSoldView.as_view(), name='device_sell'),
    
    # Telemetry Module endpoints
    path('telemetry-modules/create/', views.TelemetryModuleCreateView.as_view(), name='telemetry_module_create'),
    
    # Device-Telemetry Module relationship endpoints
    path('device-telemetry/link/', views.DeviceTelemetryModuleLinkView.as_view(), name='device_telemetry_link'),
]