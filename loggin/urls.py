from django.urls import path, include
from . import views

urlpatterns = [

    # Páginas HTML
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login_page"),
    path("register/", views.register_page, name="register_page"),
    path("recovery-password/", views.recovery_password_page, name="recovery_password_page"),
    path("reset-password/", views.reset_password_page, name="reset_password_page"),
    path("edit-profile/", views.edit_profile_page, name="edit_profile_page"),

    #API
    path("api/web/v0/", include("users.api.web.v0.urls")), # APIs web
    path("api/mobile/v0/", include("users.api.mobile.v0.urls")), # APIs mobile
]