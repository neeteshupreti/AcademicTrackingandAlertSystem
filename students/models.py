from django.db import models

class Student(models.Model):
    """Stores general student information, typically extracted once."""
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    batch = models.CharField(max_length=20)
    
    # Current academic position
    current_year = models.IntegerField(null=True, blank=True, default=1, help_text="Student's current year (1-4)")
    current_semester = models.IntegerField(null=True, blank=True, default=1, help_text="Student's current semester (1-8)")
    
    # GPA can vary per semester, but we store the latest/overall GPA
    gpa = models.FloatField(default=0.0, null=True, blank=True, help_text="Latest or overall GPA")
    email = models.EmailField(unique=True, null=True, blank=True)

    # Metadata for tracking
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class CompartExamRecord(models.Model):
    """
    Stores a record of a specific failed subject for a student,
    indicating their eligibility for a compartment exam.
    
    Supports multiple compartments across different semesters for the same student.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='compart_records')
    
    # Subject information
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=100, blank=True, null=True)
    grade = models.CharField(max_length=5, default='F', help_text="The grade received (typically F or INC)")
    
    # Year and Semester information (allows multiple compartments from different semesters)
    year = models.IntegerField(default=1, help_text="Academic year in which student failed (1-4)")
    semester = models.IntegerField(default=1, help_text="Semester in which student failed the subject (1-8)")
    
    # GPA at time of failure
    gpa_at_failure = models.FloatField(null=True, blank=True, help_text="Student's GPA when they failed this subject")
    
    # Tracking the origin (which GPA sheet this came from)
    gpa_sheet_file = models.CharField(max_length=255, blank=True)

    # Compartment exam dates and deadlines
    registration_deadline = models.DateTimeField(null=True, blank=True, help_text="Deadline for compartment registration")
    exam_date = models.DateTimeField(null=True, blank=True, help_text="Date and time of compartment exam")
    
    # Notification tracking
    registration_deadline_notified = models.BooleanField(default=False, help_text="Has registration deadline notification been sent?")
    exam_date_notified = models.BooleanField(default=False, help_text="Has exam date notification been sent?")

    # Status tracking for the student's attempt
    is_cleared = models.BooleanField(default=False, help_text="Did student clear the compartment exam?")
    
    # Timestamp
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Allow multiple records for same subject if from different semesters/years
        # A student can have at most one record per subject per year/semester combination
        unique_together = ('student', 'subject_code', 'year', 'semester', 'grade')
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['student', 'year', 'semester']),
            models.Index(fields=['semester', 'is_cleared']),
        ]

    def __str__(self):
        return f"{self.student.registration_number} - {self.subject_code} (Year {self.year}, Sem {self.semester})"


class CompartExamConfig(models.Model):
    """
    Global configuration for compartmental exams.
    Stores exam deadlines, dates, and alert timings that apply to all students.
    """
    subject_code = models.CharField(max_length=50, unique=True, help_text="Subject code (e.g., COMP102, MATH101)")
    subject_name = models.CharField(max_length=100, blank=True, help_text="Full subject name")
    
    # Exam dates and deadlines - apply to all students taking this compartment
    registration_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text="Registration deadline for compartment exam"
    )
    exam_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Date and time of compartment exam"
    )
    exam_duration_minutes = models.IntegerField(
        default=180,
        help_text="Duration of exam in minutes"
    )
    
    # Alert timing configuration - when to send notifications
    registration_alert_days_before = models.IntegerField(
        default=7,
        help_text="Send registration deadline alert X days before deadline"
    )
    exam_alert_days_before = models.IntegerField(
        default=3,
        help_text="Send exam schedule alert X days before exam"
    )
    exam_alert_hours_before = models.IntegerField(
        default=24,
        help_text="Also send exam reminder X hours before exam (if different from days)"
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Is this compartment active?")
    
    # Additional info
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or instructions for this compartment exam"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['subject_code']
        verbose_name = "Compartment Exam Configuration"
        verbose_name_plural = "Compartment Exam Configurations"
    
    def __str__(self):
        return f"{self.subject_code} - {self.subject_name or 'Unnamed'}"

from django.db import models

class ScannedResult(models.Model):
    image = models.ImageField(upload_to='scans/') # Make sure this is indented!
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} - {self.uploaded_at}"