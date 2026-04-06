from django.contrib import admin
from .models import Student, CompartExamRecord, CompartExamConfig

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration_number', 'batch', 'current_year', 'current_semester', 'gpa', 'email']
    search_fields = ['name', 'registration_number', 'email']
    list_filter = ['batch', 'current_year', 'current_semester', 'is_active']
    readonly_fields = ['date_joined']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'registration_number', 'email')
        }),
        ('Academic Information', {
            'fields': ('batch', 'current_year', 'current_semester', 'gpa')
        }),
        ('Status', {
            'fields': ('is_active', 'date_joined')
        }),
    )


@admin.register(CompartExamRecord)
class CompartExamRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject_code', 'year_semester_display', 'subject_name', 'grade', 'exam_date', 'is_cleared']
    search_fields = ['student__name', 'student__registration_number', 'subject_code', 'subject_name']
    list_filter = ['year', 'semester', 'grade', 'is_cleared', 'registration_deadline_notified', 'exam_date_notified']
    readonly_fields = ['gpa_sheet_file', 'registration_deadline_notified', 'exam_date_notified', 'date_created', 'year_semester_info', 'auto_filled_notice']
    
    fieldsets = (
        ('Student & Subject Information', {
            'fields': ('student', 'subject_code', 'subject_name', 'grade')
        }),
        ('Academic Semester', {
            'fields': ('year', 'semester', 'year_semester_info'),
            'description': 'Year (1-4) and Semester (1-8) when subject was failed. Uses standard KU mapping.'
        }),
        ('GPA Information', {
            'fields': ('gpa_at_failure',),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('registration_deadline', 'exam_date', 'auto_filled_notice'),
            'description': 'Dates are auto-populated from Compartment Exam Configuration. Edit here to override for specific cases.'
        }),
        ('Notification Status', {
            'fields': ('registration_deadline_notified', 'exam_date_notified'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_cleared', 'gpa_sheet_file', 'date_created'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_registration_deadline_notifications', 'send_exam_date_notifications']
    
    def auto_filled_notice(self, obj):
        """Display notice about auto-filled dates."""
        if obj.registration_deadline or obj.exam_date:
            return "✓ Dates are automatically populated from Compartment Exam Configuration. Edit above to override."
        return "⚠ No dates set. Configure in 'Compartment Exam Configuration' section, or set manually here."
    auto_filled_notice.short_description = "Auto-Fill Status"
    
    def save_model(self, request, obj, form, change):
        """Auto-populate dates from CompartExamConfig if not set."""
        if not obj.pk or (not obj.registration_deadline and not obj.exam_date):
            try:
                config = CompartExamConfig.objects.get(subject_code=obj.subject_code)
                if not obj.registration_deadline and config.registration_deadline:
                    obj.registration_deadline = config.registration_deadline
                if not obj.exam_date and config.exam_date:
                    obj.exam_date = config.exam_date
                if not obj.subject_name and config.subject_name:
                    obj.subject_name = config.subject_name
            except CompartExamConfig.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)
    
    def year_semester_display(self, obj):
        """Display year and semester in formatted way"""
        # Year I/II/III/IV
        year_roman = ['', 'I', 'II', 'III', 'IV'][obj.year] if 1 <= obj.year <= 4 else str(obj.year)
        return f"Year {year_roman}, Sem {obj.semester}"
    year_semester_display.short_description = "Year/Semester"
    
    def year_semester_info(self, obj):
        """Display detailed year/semester information"""
        # Year I/II/III/IV
        year_roman = ['', 'I', 'II', 'III', 'IV'][obj.year] if 1 <= obj.year <= 4 else str(obj.year)
        
        # Semester mapping
        sem_in_year = ((obj.semester - 1) % 2) + 1
        
        info = (
            f"<strong>Academic Year {year_roman}</strong><br/>"
            f"Year {obj.year} of 4-year program<br/>"
            f"<br/>"
            f"<strong>Semester {obj.semester}</strong><br/>"
            f"Semester {sem_in_year} of Year {obj.year}"
        )
        return info
    year_semester_info.short_description = "Year/Semester Details"
    year_semester_info.allow_tags = True
    
    def send_registration_deadline_notifications(self, request, queryset):
        """Admin action to send registration deadline notifications"""
        from .email_notifications import send_registration_deadline_notification
        success_count = 0
        
        for record in queryset:
            if record.registration_deadline and not record.registration_deadline_notified:
                if send_registration_deadline_notification(record):
                    record.registration_deadline_notified = True
                    record.save()
                    success_count += 1
        
        self.message_user(request, f"✓ Sent {success_count} registration deadline notifications")
    
    send_registration_deadline_notifications.short_description = "Send registration deadline notifications"
    
    def send_exam_date_notifications(self, request, queryset):
        """Admin action to send exam date notifications"""
        from .email_notifications import send_exam_date_notification
        success_count = 0
        
        for record in queryset:
            if record.exam_date and not record.exam_date_notified:
                if send_exam_date_notification(record):
                    record.exam_date_notified = True
                    record.save()
                    success_count += 1
        
        self.message_user(request, f"✓ Sent {success_count} exam date notifications")
    
    send_exam_date_notifications.short_description = "Send exam date notifications"


@admin.register(CompartExamConfig)
class CompartExamConfigAdmin(admin.ModelAdmin):
    """Admin interface for managing compartmental exam deadlines and alert timings."""
    list_display = ['subject_code', 'subject_name', 'registration_deadline', 'exam_date', 'is_active']
    search_fields = ['subject_code', 'subject_name']
    list_filter = ['is_active', 'registration_deadline', 'exam_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('subject_code', 'subject_name'),
            'description': 'Enter the subject code and name (e.g., COMP102, Computer Programming)'
        }),
        ('Examination Schedule', {
            'fields': ('registration_deadline', 'exam_date', 'exam_duration_minutes'),
            'description': 'Set the registration deadline and exam date/time for all students in this compartment'
        }),
        ('Alert Timing Configuration', {
            'fields': (
                'registration_alert_days_before',
                'exam_alert_days_before',
                'exam_alert_hours_before'
            ),
            'description': 'Configure when to automatically send notifications to students'
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make timestamp fields readonly."""
        readonly = list(self.readonly_fields)
        if obj:  # Only if editing existing object
            readonly.extend(['created_at', 'updated_at'])
        return readonly