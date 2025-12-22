from django.urls import path
from . import views

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
        views.MobileTokenRefreshView.as_view(),
        name="api_mobile_token_refresh",
    ),
    path("me/", views.MeView.as_view(), name="api_mobile_me"),
    path(
        "me/permissions/",
        views.UserPermissionsView.as_view(),
        name="api_mobile_me_permissions",
    ),
    path(
        "me/group/",
        views.MeGroupView.as_view(),
        name="api_mobile_me_group",
    ),
    path(
        "assign-role/",
        views.AssignUserRoleView.as_view(),
        name="api_mobile_assign_role",
    ),
    # Gerenciamento de imagens de perfil para mobile
    path(
        "profile/image/",
        views.manage_profile_image,
        name="api_mobile_profile_image",
    ),  # POST/DELETE - gerenciar imagem
    path(
        "profile/image/<int:user_id>/",
        views.serve_profile_image,
        name="api_mobile_serve_profile_image",
    ),  # GET - servir imagem como proxy
    # Patient relationship management
    path(
        "me/patients/",
        views.my_patients,
        name="api_mobile_my_patients",
    ),  # GET - listar meus pacientes
    path(
        "me/patients/add/",
        views.add_patient_to_care,
        name="api_mobile_add_patient",
    ),  # POST - adicionar paciente existente aos cuidados
    path(
        "me/patients/<uuid:patient_id>/remove/",
        views.remove_patient_from_care,
        name="api_mobile_remove_patient",
    ),  # DELETE - remover paciente
]
