from django.urls import path, include

urlpatterns = [
    path('api/web/v0/', include('devices.api.web.v0.urls')),
    path('api/mobile/v0/', include('devices.api.mobile.v0.urls')),
]