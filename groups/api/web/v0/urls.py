from django.urls import path
from . import views

urlpatterns = [
    # Groups
    path('groups/', views.GroupListView.as_view(), name='groups_list'),  # GET
    path('groups/create/', views.GroupCreateView.as_view(), name='groups_create'),  # POST
    path('groups/<uuid:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<uuid:group_id>/clinics/', views.GroupClinicsView.as_view(), name='group_clinics'),
    path('groups/<uuid:group_id>/devices/', views.GroupDevicesView.as_view(), name='group_devices'),
    
    # Clinics
    path('clinics/', views.ClinicCreateView.as_view(), name='clinic_create'),
    path('clinics/<uuid:pk>/', views.ClinicDetailView.as_view(), name='clinic_detail'),
    path('clinics/<uuid:clinic_id>/devices/', views.ClinicDevicesView.as_view(), name='clinic_devices'),
    path('clinics/<uuid:clinic_id>/users/', views.ClinicUsersView.as_view(), name='clinic_users'),
    
    # User-Clinic associations
    path('user-clinics/', views.UserClinicCreateView.as_view(), name='user_clinic_create'),
    path('user-clinics/<uuid:pk>/', views.UserClinicDeleteView.as_view(), name='user_clinic_delete'),
]