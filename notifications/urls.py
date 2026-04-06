from django.urls import path
from . import views

urlpatterns = [
    path('set-deadline/', views.set_deadline, name='set_deadline'),
    path('send-bulk-alerts/', views.send_bulk_alerts, name='send_bulk_alerts'),
    path('send-quick-alert/', views.send_quick_alert, name='send_quick_alert'),
    path('api/get-students/', views.get_students_by_year_semester, name='get_students'),
]