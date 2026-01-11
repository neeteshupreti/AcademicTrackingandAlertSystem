from django.urls import path
from . import views

urlpatterns = [
    path('set-deadline/', views.set_deadline, name='set_deadline'),
]