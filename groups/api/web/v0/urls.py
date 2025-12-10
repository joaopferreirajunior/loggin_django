from django.urls import path
from . import views

urlpatterns = [
    # Groups
    path('groups/', views.GroupListView.as_view(), name='groups_list'),
    path('groups/<uuid:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<uuid:group_id>/clinics/', views.GroupClinicsView.as_view(), name='group_clinics'),
    path('groups/<uuid:group_id>/devices/', views.GroupDevicesView.as_view(), name='group_devices'),
    
    # Clinics
    path('clinics/<uuid:pk>/', views.ClinicDetailView.as_view(), name='clinic_detail'),
    path('clinics/<uuid:clinic_id>/devices/', views.ClinicDevicesView.as_view(), name='clinic_devices'),
]