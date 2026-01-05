from django.urls import path
from . import views

urlpatterns = [
    # Groups
    path('groups/', views.GroupListView.as_view(), name='mobile_groups_list'),  # GET
    path('groups/create/', views.GroupCreateView.as_view(), name='mobile_groups_create'),  # POST
    path('groups/<uuid:pk>/', views.GroupDetailView.as_view(), name='mobile_group_detail'),
    path('groups/<uuid:group_id>/clinics/', views.GroupClinicsView.as_view(), name='mobile_group_clinics'),
    path('groups/<uuid:group_id>/devices/', views.GroupDevicesView.as_view(), name='mobile_group_devices'),
    
    # Clinics
    path('clinics/', views.ClinicCreateView.as_view(), name='mobile_clinic_create'),
    path('clinics/<uuid:pk>/', views.ClinicDetailView.as_view(), name='mobile_clinic_detail'),
    path('clinics/<uuid:clinic_id>/devices/', views.ClinicDevicesView.as_view(), name='mobile_clinic_devices'),
    path('clinics/<uuid:clinic_id>/uploadImage/', views.MobileClinicImageUploadView.as_view(), name='mobile_clinic_image_upload'),
    
    # User-Clinic associations
    path('user-clinics/', views.UserClinicCreateView.as_view(), name='mobile_user_clinic_create'),
    path('user-clinics/<uuid:pk>/', views.UserClinicDeleteView.as_view(), name='mobile_user_clinic_delete'),
]