from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_gpa_sheet, name='upload_gpa'),
    path('list/', views.compartment_students_list, name='compartment_students'),
]