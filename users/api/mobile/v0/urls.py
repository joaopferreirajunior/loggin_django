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
        "assign-role/",
        views.AssignUserRoleView.as_view(),
        name="api_mobile_assign_role",
    ),
    # Gerenciamento de imagens de perfil para mobile
    path(
        "profile/image/",
        views.MobileProfileImageUploadView.as_view(),
        name="api_mobile_profile_image",
    ),
    path(
        "profile/image/delete/",
        views.MobileProfileImageDeleteView.as_view(),
        name="api_mobile_profile_image_delete",
    ),
    path(
        "profile/image/serve/<int:user_id>/",
        views.MobileServeProfileImageView.as_view(),
        name="api_mobile_profile_image_serve",
    ),
    # Patient relationship management
    path(
        "my-patients/",
        views.my_patients,
        name="api_mobile_my_patients",
    ),  # GET - listar meus pacientes
    path(
        "add-patient/",
        views.add_patient_to_care,
        name="api_mobile_add_patient",
    ),  # POST - adicionar paciente aos cuidados
    path(
        "remove-patient/<uuid:relation_id>/",
        views.remove_patient_from_care,
        name="api_mobile_remove_patient",
    ),  # DELETE - remover paciente
    path(
        "patient-doctors/<uuid:patient_id>/",
        views.patient_doctors,
        name="api_mobile_patient_doctors",
    ),  # GET - profissionais que atendem um paciente
]
