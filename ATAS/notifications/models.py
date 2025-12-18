from django.db import models

class CompartDeadline(models.Model):
    """Defines a specific compartment exam cycle and its deadline."""
    cycle_name = models.CharField(max_length=100, help_text="e.g., 'Fall 2025 Compart Exam'")
    semester_affected = models.IntegerField(help_text="The semester the failed subjects belong to.")
    
    form_deadline = models.DateField(help_text="The final date for form submission.")
    
    # Notification tracking
    alert_date = models.DateField(blank=True, null=True, help_text="Calculated date (7 days before deadline) for sending the alert.")
    is_alert_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Automatically calculates the alert date."""
        from datetime import timedelta
        if self.form_deadline:
            self.alert_date = self.form_deadline - timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cycle_name} (Deadline: {self.form_deadline})"