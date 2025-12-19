from django.contrib import admin
from django.urls import path, include
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('students/', include('students.urls')),
    path('notifications/', include('notifications.urls')),
]