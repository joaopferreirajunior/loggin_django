from django.urls import path, include

urlpatterns = [
    path('api/web/v0/', include('patients.api.web.v0.urls')),
    path('api/mobile/v0/', include('patients.api.mobile.v0.urls')),
]
