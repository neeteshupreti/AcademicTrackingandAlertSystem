from django import forms

class GpaSheetUploadForm(forms.Form):
    """Form for uploading image or PDF files of GPA sheets."""
    gpa_file = forms.FileField(
        label='Select GPA Sheet (Image/PDF)',
        help_text='Supported formats: JPG, PNG, PDF.',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    semester = forms.IntegerField(
        label='Semester of GPA Sheet',
        help_text='e.g., 3',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )