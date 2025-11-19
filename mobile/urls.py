from django.urls import path, include

urlpatterns = [
    #API
    path("api/v0/", include("mobile.api.v0.urls")), # APIs do app mobile
]