from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets mobile (REST padrão)
router = DefaultRouter()
router.register(r'devices', views.MobileDeviceViewSet, basename='mobile_device')
router.register(r'device-models', views.MobileDeviceModelViewSet, basename='mobile_devicemodel')
router.register(r'device-features', views.MobileDeviceFeaturesViewSet, basename='mobile_devicefeatures')
router.register(r'device-leases', views.MobileDeviceLeaseViewSet, basename='mobile_devicelease')

urlpatterns = [
    # ViewSets - inclui rotas automáticas REST
    path('', include(router.urls)),
    
    # Device endpoints - Views customizadas mobile (mantidas para compatibilidade)
    path('devices/<uuid:deviceId>/tested/', views.MobileDeviceTestView.as_view(), name='mobile_device_test'),
    path('devices/<uuid:deviceId>/sold/', views.MobileDeviceSoldView.as_view(), name='mobile_device_sell'),
    
    # Device Location endpoints (mobile)
    path('devices/locations/', views.MobileDeviceLocationCreateView.as_view(), name='mobile_device_location_create'),
    path('devices/locations/global/', views.MobileDeviceGlobalLocationsView.as_view(), name='mobile_device_global_locations'),
    path('devices/locations/<uuid:deviceId>/', views.MobileDeviceLocationsListView.as_view(), name='mobile_device_locations_list'),
    
    # Telemetry Module endpoints (mobile)
    path('modules/', views.MobileTelemetryModuleCreateView.as_view(), name='mobile_telemetry_module_create'),
    path('modules/<uuid:moduleId>/', views.MobileTelemetryModuleDetailView.as_view(), name='mobile_telemetry_module_detail'),
    
    # Device-Telemetry Module relationship endpoints (mobile)
    path('devices/link-module/', views.MobileDeviceTelemetryModuleLinkView.as_view(), name='mobile_device_telemetry_link'),
]