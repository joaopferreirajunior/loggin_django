from django.urls import path, include
from . import views

urlpatterns = [

    # Páginas HTML
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login_page"),
    path("register/", views.register_page, name="register_page"),
    path("edit-profile/", views.edit_profile_page, name="edit_profile_page"),

    #API
    path("api/v0/", include("web.api.v0.urls")), # APIs do app web
]