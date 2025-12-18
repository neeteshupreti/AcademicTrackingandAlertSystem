import os
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import Student, CompartExamRecord
from .forms import GpaSheetUploadForm # We will define this next

# --- Conceptual OCR/Data Extraction Functions ---
# NOTE: These functions must be implemented using Pytesseract/PaddleOCR and OpenCV.

def preprocess_image(file_path):
    """Placeholder: Uses OpenCV to clean up the image before OCR."""
    # Logic to deskew, denoise, and enhance contrast goes here.
    return file_path # Returns the path to the cleaned image

def run_ocr_and_extract_data(image_path):
    """
    Placeholder: Runs OCR and parses the text into a structured list of dictionaries.
    Returns: List of dicts: [{'reg_no': '...', 'name': '...', 'grade': 'F', ...}, ...]
    """
    # 1. Run OCR (e.g., pytesseract.image_to_string)
    # 2. Use Regular Expressions to parse the raw text into structured data.
    # 3. Use Pandas to normalize and filter the data.
    
    # Placeholder for failed students data (must have 'F' grade)
    extracted_data = [
        {'reg_no': '12345', 'name': 'Alice Smith', 'semester': 3, 'batch': '2023', 'sub_code': 'CS401', 'grade': 'F', 'email': 'alice@test.edu'},
        {'reg_no': '67890', 'name': 'Bob Johnson', 'semester': 3, 'batch': '2023', 'sub_code': 'MT402', 'grade': 'F', 'email': 'bob@test.edu'},
        # Add more logic to handle cases where grade != 'F'
    ]
    return extracted_data

# -----------------------------------------------

@require_http_methods(["GET", "POST"])
def upload_gpa_sheet(request):
    """Handles the file upload and initiates the OCR process."""
    if request.method == 'POST':
        form = GpaSheetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['gpa_file']
            
            # 1. Save the file temporarily
            file_path = os.path.join(settings.MEDIA_ROOT, 'gpa_uploads', uploaded_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # 2. Run Pre-processing and OCR
            cleaned_path = preprocess_image(file_path)
            failed_students_data = run_ocr_and_extract_data(cleaned_path)
            
            records_created = 0
            
            # 3. Save Data to Database
            for record in failed_students_data:
                if record['grade'] == 'F':
                    # Get or Create the Student record
                    student, created = Student.objects.get_or_create(
                        registration_number=record['reg_no'],
                        defaults={
                            'name': record['name'], 
                            'batch': record['batch'], 
                            'semester': record['semester'],
                            'email': record['email'],
                        }
                    )
                    
                    # Create the Compart Record
                    CompartExamRecord.objects.get_or_create(
                        student=student,
                        subject_code=record['sub_code'],
                        defaults={
                            'grade': record['grade'],
                            'gpa_sheet_file': uploaded_file.name,
                        }
                    )
                    records_created += 1

            # 4. Cleanup (optional: delete the uploaded file)
            # os.remove(file_path)
            
            # 5. Success Message and Redirect
            from django.contrib import messages
            messages.success(request, f"GPA Sheet processed successfully. {records_created} compartment records found and saved.")
            return redirect('compartment_students') # Redirect to the list view
    else:
        form = GpaSheetUploadForm()
        
    context = {'form': form, 'page_title': 'Upload GPA Sheet'}
    return render(request, 'students/upload_gpa.html', context)

# --- Other views (like compartment_students, home) will be added later ---