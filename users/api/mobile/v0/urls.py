from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", views.login_view, name="api_mobile_login"),
    path("logout/", views.logout_view, name="api_mobile_logout"),
    path("register/", views.register, name="api_mobile_register"),
    path(
        "recoverypassword/",
        views.recovery_password,
        name="api_mobile_recovery_password",
    ),
    path(
        "resetpassword/",
        views.reset_password,
        name="api_mobile_reset_password",
    ),
    path(
        "validatetoken/",
        views.validate_token,
        name="api_mobile_validate_token",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="api_mobile_token_refresh",
    ),
    path("me/", views.MeView.as_view(), name="api_mobile_me"),
    path(
        "me/profile/",
        views.MeProfileView.as_view(),
        name="api_mobile_me_profile",
    ),
    path(
        "me/permissions/",
        views.UserPermissionsView.as_view(),
        name="api_mobile_me_permissions",
    ),
    path(
        "assign-role/",
        views.AssignUserRoleView.as_view(),
        name="api_mobile_assign_role",
    ),
]
