from django.db import models

class Faculty(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.EmailField()

    def __clstr__(self):
        return self.name

class Course(models.Model):
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

class CompartDeadline(models.Model):
    cycle_name = models.CharField(max_length=100)
    # New relational fields
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    
    semester_affected = models.CharField(max_length=50)
    form_deadline = models.DateTimeField()
    alert_date = models.DateTimeField()
    is_alert_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cycle_name