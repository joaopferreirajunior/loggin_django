from django.urls import path
from . import views

urlpatterns = [
    # Patients endpoints (REST style)
    path('', views.manage_patients_list, name='api_web_patients'),
    path('<uuid:patient_id>/', views.manage_patient_detail, name='api_web_patient_detail'),
    
    # Medical Records endpoints
    path('mrecords/<uuid:patient_id>/', views.manage_medical_records, name='api_web_medical_records'),
    path('mrecords/<uuid:record_id>/', views.update_medical_record, name='api_web_medical_records_update'),
    
    # Anamnesis endpoints
    path('anamnesis/<uuid:patient_id>/', views.manage_anamnesis_by_patient, name='api_web_anamnesis_by_patient'),
    path('anamnesis/<uuid:anamnesis_id>/', views.manage_anamnesis_by_id, name='api_web_anamnesis_by_id'),
    
    # Patient Photo endpoints
    path('image/<uuid:patient_id>/', views.manage_patient_photo, name='api_web_patient_image'),
    
    # Patient Doctors endpoints
    path('doctors/<uuid:patient_id>/', views.get_patient_doctors, name='api_web_patient_doctors'),
]