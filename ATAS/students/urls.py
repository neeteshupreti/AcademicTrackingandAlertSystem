from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_gpa_sheet, name='upload_gpa'),
    path('list/', views.compartment_students_list, name='compartment_students'),
    path('import-records/', views.import_records_view, name='upload_gpa'), # This name must match your header link
    path('process-scan/', views.process_scan, name='process_scan'),
]