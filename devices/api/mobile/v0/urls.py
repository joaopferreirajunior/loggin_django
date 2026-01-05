from django.urls import path
from . import views

urlpatterns = [
    # Device endpoints (mobile format with camelCase)
    path('devices/create/', views.MobileDeviceCreateView.as_view(), name='mobile_device_create'),
    path('devices/<uuid:deviceId>/tested/', views.MobileDeviceTestView.as_view(), name='mobile_device_test'),
    path('devices/<uuid:deviceId>/sold/', views.MobileDeviceSoldView.as_view(), name='mobile_device_sell'),
    
    # Telemetry Module endpoints (mobile)
    path('telemetryModules/create/', views.MobileTelemetryModuleCreateView.as_view(), name='mobile_telemetry_module_create'),
    
    # Device-Telemetry Module relationship endpoints (mobile)
    path('deviceTelemetry/link/', views.MobileDeviceTelemetryModuleLinkView.as_view(), name='mobile_device_telemetry_link'),
]