from django.urls import path, include
from . import views

urlpatterns = [
    #API
    path("api/mobile/v0/", include("users.api.mobile.v0.urls")), # APIs do app users
    path("api/web/v0/", include("users.api.web.v0.urls")), # APIs do app users
    path("api/legacy/", include("users.api.legacy.urls")), # API para integração com sistema legado
]