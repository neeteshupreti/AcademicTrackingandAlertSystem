from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_gpa_sheet, name='upload_gpa'),
    path('scan/', views.import_records_view, name='import_records'),
    path('process-scan/', views.process_scan, name='process_scan'),
    path('save-verified/', views.save_verified_data, name='save_verified'),
    path('list/', views.compartment_students_list, name='compartment_students'),
]