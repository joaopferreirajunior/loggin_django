from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("web.urls")),                 # páginas HTML e APIs do web
    path("admin/", admin.site.urls),                # admin
    path("mobile/", include("mobile.urls")),   # APIs do app mobile  
    path("users/", include("users.urls")), # APIs do app users
]