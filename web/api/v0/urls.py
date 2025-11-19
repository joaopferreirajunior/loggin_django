from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='api_web_login'),
    path('logout/', views.logout_view, name='api_web_logout'),
    path('register/', views.register, name='api_web_register'),
    path("me/", views.MeView.as_view(), name="api_web_me"),  # GET - dados básicos do usuário
    path("me/profile/", views.MeProfileView.as_view(), name="api_web_me_profile"),  # GET/PATCH - dados do perfil
    path("me/permissions/", views.UserPermissionsView.as_view(), name="api_web_me_permissions"),  # GET - permissões do usuário
    path("assign-role/", views.AssignUserRoleView.as_view(), name="api_web_assign_role"),  # POST - atribuir papel
]