from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets REST
router = DefaultRouter()
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'device-models', views.DeviceModelViewSet, basename='devicemodel')
router.register(r'device-features', views.DeviceFeaturesViewSet, basename='devicefeatures')
router.register(r'device-leases', views.DeviceLeaseViewSet, basename='devicelease')

urlpatterns = [
    # ViewSets registrados no router (gera endpoints REST automaticamente)
    path('', include(router.urls)),
    
    # Device endpoints (views antigas - manter compatibilidade se necessário)
    path('devices/with-telemetry/', views.DeviceWithTelemetryCreateView.as_view(), name='device_with_telemetry_create'),
    path('devices/<uuid:device_id>/events/', views.DeviceEventCreateView.as_view(), name='device_event_create'),
    path('devices/<uuid:device_id>/events/list/', views.DeviceEventListView.as_view(), name='device_event_list'),
    
    # Device Location endpoints
    path('locations/', views.DeviceLocationsView.as_view(), name='device_all_locations'),
    path('devices/locations/', views.DeviceLocationCreateView.as_view(), name='device_location_create'),
    path('devices/locations/global/', views.DeviceGlobalLocationsView.as_view(), name='device_global_locations'),
    path('devices/locations/<uuid:device_id>/', views.DeviceLocationsListView.as_view(), name='device_locations_list'),
    
    # Telemetry Module endpoints
    path('modules/', views.TelemetryModuleCreateView.as_view(), name='telemetry_module_create'),
    path('modules/<uuid:module_id>/', views.TelemetryModuleDetailView.as_view(), name='telemetry_module_detail'),
    
    # Device-Telemetry Module relationship endpoints
    path('devices/link-module/', views.DeviceTelemetryModuleLinkView.as_view(), name='device_telemetry_link'),
]
