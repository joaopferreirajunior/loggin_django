from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='api_app_login'),
    path('logout/', views.logout_view, name='api_app_logout'),
    path('register/', views.register, name='api_app_register'),
]