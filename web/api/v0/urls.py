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
    path("me/", views.MeView.as_view(), name="api_web_me"),  # GET - dados básicos do usuário
    path("me/profile/", views.MeProfileView.as_view(), name="api_web_me_profile"),  # GET/PATCH - dados do perfil
    path("me/permissions/", views.UserPermissionsView.as_view(), name="api_web_me_permissions"),  # GET - permissões do usuário
    path("assign-role/", views.AssignUserRoleView.as_view(), name="api_web_assign_role"),  # POST - atribuir papel
]