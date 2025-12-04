from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', views.login_view, name='api_web_login'),
    path('logout/', views.logout_view, name='api_web_logout'),
    path('register/', views.register, name='api_web_register'),
    path('recoverypassword/', views.recovery_password, name='api_web_recovery_password'),
    path('resetpassword/', views.reset_password, name='api_web_reset_password'),
    path('validatetoken/', views.validate_token, name='api_web_validate_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api_web_token_refresh'),
    
    # User data endpoints
    path("me/", views.get_current_user, name="api_web_current_user"),  # GET - dados básicos do usuário
    path("me/profile/", views.get_current_user_profile, name="api_web_current_user_profile"),  # GET/PATCH - dados completos do perfil
    path("me/permissions/", views.get_user_permissions, name="api_web_user_permissions"),  # GET - permissões do usuário
    
    # Role management
    path("assign-role/", views.assign_role, name="api_web_assign_role"),  # POST - atribuir papel
    
    # Profile image management  
    path("profile/image/", views.manage_profile_image, name="api_web_profile_image"),  # POST/DELETE - gerenciar imagem
]