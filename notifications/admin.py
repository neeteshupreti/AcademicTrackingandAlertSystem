from django.contrib import admin
from .models import Faculty, Course, CompartDeadline

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'email')
    search_fields = ('name', 'department')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'faculty')
    list_filter = ('faculty',)

@admin.register(CompartDeadline)
class CompartDeadlineAdmin(admin.ModelAdmin):
    list_display = ('cycle_name', 'course', 'assigned_faculty', 'form_deadline', 'is_alert_sent')
    list_filter = ('is_alert_sent', 'course')