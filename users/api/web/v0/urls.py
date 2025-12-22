from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='api_web_login'),
    path('logout/', views.logout_view, name='api_web_logout'),
    path('register/', views.register, name='api_web_register'),
    path('recoverypassword/', views.recovery_password, name='api_web_recovery_password'),
    path('resetpassword/', views.reset_password, name='api_web_reset_password'),
    path('validatetoken/', views.validate_token, name='api_web_validate_token'),
    path('token/refresh/', views.WebTokenRefreshView.as_view(), name='api_web_token_refresh'),
    
    # User data endpoints
    path("me/", views.get_current_user, name="api_web_current_user"),  # GET/PATCH - dados completos do usuário com perfil
    path("me/permissions/", views.get_user_permissions, name="api_web_user_permissions"),  # GET - permissões do usuário
    path("me/group/", views.get_me_group, name="api_web_me_group"),  # GET - grupo e clínicas do usuário
    
    # Role management
    path("assign-role/", views.assign_role, name="api_web_assign_role"),  # POST - atribuir papel
    
    # Profile image management  
    path("profile/image/", views.manage_profile_image, name="api_web_profile_image"),  # POST/DELETE - gerenciar imagem
    path("profile/image/<int:user_id>/", views.serve_profile_image, name="api_web_serve_profile_image"),  # GET - servir imagem como proxy
    
    # Patient relationship management
    path("me/patients/", views.my_patients, name="api_web_my_patients"),  # GET - listar meus pacientes
    path("me/patients/add/", views.add_patient_to_care, name="api_web_add_patient"),  # POST - adicionar paciente existente aos cuidados
    path("me/patients/<uuid:patient_id>/remove/", views.remove_patient_from_care, name="api_web_remove_patient"),  # DELETE - remover paciente
]