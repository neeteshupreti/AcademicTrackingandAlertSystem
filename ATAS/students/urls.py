from django.urls import path
from . import views

urlpatterns = [
    path('upload-gpa/', views.upload_gpa_sheet, name='upload_gpa'),
    # path('compartment-students/', views.compartment_students_list, name='compartment_students'), # To be implemented next
]