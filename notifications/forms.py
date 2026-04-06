from django import forms
from django.forms import ModelMultipleChoiceField
from .models import CompartDeadline
from students.models import Student


class CompartDeadlineForm(forms.ModelForm):
    class Meta:
        model = CompartDeadline
        fields = ['cycle_name', 'semester_affected', 'form_deadline']
        widgets = {
            'cycle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'semester_affected': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
            'form_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'cycle_name': 'Exam Cycle Name',
            'semester_affected': 'Semester Failed',
            'form_deadline': 'Form Submission Deadline',
        }


class BulkAlertForm(forms.Form):
    """
    Form for sending alerts to multiple students about specific subjects.
    Supports three types of alerts:
    1. Failing Record Alert - informing about failed subjects
    2. Compartment Registration Deadline - reminder for registration deadline
    3. Compartment Exam Date - reminder for exam date
    """
    
    ALERT_TYPE_CHOICES = [
        ('failing_record', 'Failing Record Alert - Inform students of failed subjects'),
        ('compart_registration', 'Compartment Registration Deadline - Registration reminder'),
        ('compart_exam', 'Compartment Exam Date - Exam date reminder'),
    ]
    
    # Year selection (filter by year)
    year = forms.ChoiceField(
        choices=[('', '-- Select Year --')] + [(i, f'Year {i}') for i in range(1, 5)],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_year'}),
        label='Academic Year',
        required=False,
    )
    
    # Semester selection (filter by semester)
    semester = forms.ChoiceField(
        choices=[('', '-- Select Semester --')] + [(i, f'Semester {i}') for i in range(1, 9)],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_semester'}),
        label='Semester',
        required=False,
    )
    
    # Student selection (multiple) - will be populated via AJAX
    students = ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True).order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        label='Select Students',
        help_text='Choose one or more students to send alerts to',
        required=True,
    )
    
    # Subject selection (optional, for specific subjects)
    subjects = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Enter subject codes separated by commas (e.g., COMP102, MATH101)\nLeave empty to alert about all failed subjects',
            'class': 'form-control',
        }),
        label='Specific Subjects (Optional)',
        help_text='Leave empty to include all failed subjects for selected students. Separate codes with commas.'
    )
    
    # Alert type selection
    alert_type = forms.ChoiceField(
        choices=ALERT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label='Alert Type',
        help_text='Choose what type of alert to send',
    )
    
    # Custom message (optional)
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter custom message to include in alerts (optional)',
            'class': 'form-control',
        }),
        label='Custom Message (Optional)',
        help_text='Add a custom message to include in the alert emails'
    )
    
    # Send test email first
    send_test = forms.BooleanField(
        required=False,
        label='Send Test Email First',
        help_text='Check this to send a test email to your address before sending to all students'
    )
    
    def clean_subjects(self):
        """Clean and validate subject codes"""
        subjects_str = self.cleaned_data.get('subjects', '').strip()
        
        if not subjects_str:
            return []
        
        # Split by comma and clean up
        subjects = [s.strip().upper() for s in subjects_str.split(',') if s.strip()]
        
        # Validate subject codes format (e.g., COMP102, MATH 101)
        for subject in subjects:
            # Remove spaces and validate format
            clean_subject = subject.replace(' ', '')
            # Should be 4-7 chars (e.g., MATH101, COMP102, ENG1001)
            if not (4 <= len(clean_subject) <= 7):
                raise forms.ValidationError(
                    f"Invalid subject code format: '{subject}'. "
                    f"Expected format like 'COMP102' or 'MATH 101'"
                )
        
        return subjects


class QuickAlertForm(forms.Form):
    """
    Simplified form for quick alerts to specific students.
    """
    
    # Year selection
    year = forms.ChoiceField(
        choices=[('', '-- Select Year --')] + [(i, f'Year {i}') for i in range(1, 5)],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_year_quick'}),
        label='Academic Year',
        required=False,
    )
    
    # Semester selection
    semester = forms.ChoiceField(
        choices=[('', '-- Select Semester --')] + [(i, f'Semester {i}') for i in range(1, 9)],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_semester_quick'}),
        label='Semester',
        required=False,
    )
    
    students = ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label='Select Students',
        required=True,
    )
    
    subject = forms.CharField(
        max_length=50,
        required=False,
        label='Subject Code',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., COMP102',
            'class': 'form-control'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Message to send to students',
            'class': 'form-control'
        }),
        label='Alert Message',
        help_text='Message to send to students'
    )
    
    email_recipients = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Additional email addresses to notify (one per line)',
            'class': 'form-control'
        }),
        label='Additional Email Recipients',
    )
    
    def clean_email_recipients(self):
        """Validate additional email addresses"""
        emails_str = self.cleaned_data.get('email_recipients', '').strip()
        
        if not emails_str:
            return []
        
        emails = [e.strip() for e in emails_str.split('\n') if e.strip()]
        
        # Simple email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if not re.match(email_pattern, email):
                raise forms.ValidationError(f"Invalid email address: {email}")
        
        return emails