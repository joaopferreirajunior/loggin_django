from django.urls import path
from . import views

urlpatterns = [
    # Patients endpoints
    path('', views.list_patients, name='api_web_patients_list'),
    path('create/', views.create_patient, name='api_web_patients_create'),
    path('<uuid:patient_id>/', views.get_patient, name='api_web_patients_detail'),
    path('<uuid:patient_id>/update/', views.update_patient, name='api_web_patients_update'),
    path('<uuid:patient_id>/delete/', views.delete_patient, name='api_web_patients_delete'),
    
    # Medical Records endpoints
    path('<uuid:patient_id>/records/', views.list_medical_records, name='api_web_medical_records_list'),
    path('mrecords/create/', views.create_medical_record, name='api_web_medical_records_create'),
    path('mrecords/<uuid:record_id>/update/', views.update_medical_record, name='api_web_medical_records_update'),
]