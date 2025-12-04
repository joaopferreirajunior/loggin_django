from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("", include("loggin.urls")),                 # páginas HTML e APIs do loggin
    path("admin/", admin.site.urls),                # admin
    path("users/", include("users.urls")), # APIs do app users
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"), #  Endpoint que fornece o schema OpenAPI (JSON/YAML)
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ), # Swagger UI
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ), # ReDoc UI
]