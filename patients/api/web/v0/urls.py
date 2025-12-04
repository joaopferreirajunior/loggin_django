from django.urls import path
from . import views

urlpatterns = [
    # Patients endpoints
    path('patients/', views.list_patients, name='api_web_patients_list'),
    path('patients/create/', views.create_patient, name='api_web_patients_create'),
    path('patients/<uuid:patient_id>/', views.get_patient, name='api_web_patients_detail'),
    path('patients/<uuid:patient_id>/update/', views.update_patient, name='api_web_patients_update'),
    path('patients/<uuid:patient_id>/delete/', views.delete_patient, name='api_web_patients_delete'),
    
    # Medical Records endpoints
    path('patients/<uuid:patient_id>/records/', views.list_medical_records, name='api_web_medical_records_list'),
    path('medical-records/create/', views.create_medical_record, name='api_web_medical_records_create'),
    path('medical-records/<uuid:record_id>/update/', views.update_medical_record, name='api_web_medical_records_update'),
]