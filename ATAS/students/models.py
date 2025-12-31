from django.db import models

class Student(models.Model):
    """Stores general student information, typically extracted once."""
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True)
    batch = models.CharField(max_length=20)
    semester = models.IntegerField()
    email = models.EmailField(max_length=254, unique=True, help_text="Used for automated notifications.")
    
    # Metadata for tracking
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_number} - {self.name}"

class CompartExamRecord(models.Model):
    """
    Stores a record of a specific failed subject for a student,
    indicating their eligibility for a compartment exam.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='compart_records')
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=100, blank=True, null=True)
    # The grade 'F' is implicit, but we can store the extracted grade for verification
    grade = models.CharField(max_length=5, default='F')
    
    # Tracking the origin (which GPA sheet this came from)
    gpa_sheet_file = models.CharField(max_length=255, blank=True)

    # Status tracking for the student's attempt
    is_cleared = models.BooleanField(default=False)
    
    class Meta:
        # A student should ideally only have one active compartment record per subject
        unique_together = ('student', 'subject_code', 'grade') 

    def __str__(self):
        return f"{self.student.registration_number} failed {self.subject_code}"

from django.db import models

class ScannedResult(models.Model):
    image = models.ImageField(upload_to='scans/') # Make sure this is indented!
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} - {self.uploaded_at}"