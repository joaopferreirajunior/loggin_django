from django.urls import path, include
from . import views

urlpatterns = [
    # APIs
    path("api/web/v0/", include("groups.api.web.v0.urls")),
    path("api/mobile/v0/", include("groups.api.mobile.v0.urls")),
]