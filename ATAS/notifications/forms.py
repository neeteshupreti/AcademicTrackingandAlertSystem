from django import forms
from .models import CompartDeadline

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