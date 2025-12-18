# ATAS/ATAS/urls.py
from django.contrib import admin
from django.urls import path, include
# Ensure core.views is imported correctly. If you were getting an error
# here, it's because the import chain eventually failed in core/views.py.

from core.views import home # This line is correct if core/views.py is now fixed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('students/', include('students.urls')),
    path('notifications/', include('notifications.urls')),
]