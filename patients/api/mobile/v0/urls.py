from django.urls import path
from . import views

urlpatterns = [
    # Patients endpoints (REST style)
    path('', views.manage_patients_list, name='api_mobile_patients'),
    path('<uuid:patient_id>/', views.manage_patient_detail, name='api_mobile_patient_detail'),
    
    # Medical Records endpoints
    path('<uuid:patient_id>/records/', views.list_medical_records, name='api_mobile_medical_records_list'),
    path('<uuid:patient_id>/mrecords/', views.create_medical_record, name='api_mobile_medical_records_create'),
    path('mrecords/<uuid:record_id>/', views.update_medical_record, name='api_mobile_medical_records_update'),
    
    # Patient Photo endpoints
    path('image/<uuid:patient_id>/', views.manage_patient_photo, name='api_mobile_patient_image'),
]