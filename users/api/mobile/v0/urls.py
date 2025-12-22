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
        "me/patient-association/",
        views.list_patient_associations,
        name="api_mobile_list_patient_associations",
    ),  # GET - listar pacientes
    path(
        "me/patient-association/<uuid:patient_id>/",
        views.manage_patient_association,
        name="api_mobile_manage_patient_association",
    ),  # POST/DELETE - adicionar/remover
]
