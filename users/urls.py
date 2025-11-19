from django.urls import path, include
from . import views

urlpatterns = [
    #API
    path("api/v0/", include("users.api.v0.urls")), # APIs do app users
]