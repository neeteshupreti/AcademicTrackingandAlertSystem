import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Student, CompartExamRecord

def upload_gpa_sheet(request):
    if request.method == "POST" and request.FILES.get('gpa_file'):
        file = request.FILES['gpa_file']
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)

            with transaction.atomic():
                for _, row in df.iterrows():
                    student, _ = Student.objects.update_or_create(
                        student_id=row['student_id'],
                        defaults={'name': row['name'], 'gpa': row['gpa']}
                    )

                    if row['gpa'] < 2.0:
                        # Fixed: Use 'subject_name' and 'is_cleared' per your model
                        CompartExamRecord.objects.update_or_create(
                            student=student,
                            subject_name=row.get('subject', 'General'), 
                            defaults={
                                'is_cleared': False,
                                'grade': row['gpa']
                            }
                        )
            messages.success(request, "Data processed successfully!")
            return redirect('compartment_students')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return render(request, 'students/upload_gpa.html')

def compartment_students_list(request):
    """View with dynamic filtering by semester/status."""
    records = CompartExamRecord.objects.select_related('student').all()

    # Get filter values from the URL
    semester = request.GET.get('semester')
    status = request.GET.get('status')

    if semester:
        # Assuming your student model has a semester field
        records = records.filter(student__semester=semester)
    
    if status == 'notified':
        records = records.filter(is_cleared=True)
    elif status == 'pending':
        records = records.filter(is_cleared=False)

    return render(request, 'students/compartment_list.html', {'records': records})

import re
import base64
import json
import io
from django.http import JsonResponse
from PIL import Image
import pytesseract
from .models import Student, CompartExamRecord

def process_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            format, imgstr = image_data.split(';base64,') 
            img = Image.open(io.BytesIO(base64.b64decode(imgstr)))
            
            # Extract Text
            text = pytesseract.image_to_string(img)

            # --- SYSTEMATIC PARSING ---
            
            # 1. Extract Name & Roll No (using Regex)
            name_match = re.search(r"Name of the Student\s*:\s*([\w\s]+)", text)
            roll_match = re.search(r"Examination Roll No\.\s*:\s*(\d+)", text)
            
            student_name = name_match.group(1).strip() if name_match else "Unknown"
            roll_no = roll_match.group(1).strip() if roll_match else "N/A"

            # 2. Look for Course Grades (Pattern: CODE NAME CREDIT GRADE VALUE)
            # This looks for lines like "COMP 101 ... F" or "MATH 101 ... C"
            failed_courses = []
            lines = text.split('\n')
            for line in lines:
                # If a line contains 'F' or 'D' (typical failing grades)
                if re.search(r"\b[FD]\b", line):
                    failed_courses.append(line.strip())

            # 3. Extract GPA
            # Pattern: Looks for 'GPA' followed by numbers/dots
            gpa_match = re.search(r"GPA\s*\(Grade Point Average\)\s*=\s*([\d\.]+)", text)
            gpa_value = float(gpa_match.group(1)) if gpa_match else 0.0

            # --- DECISION LOGIC ---
            status = "success"
            if gpa_value < 2.0 or len(failed_courses) > 0:
                message = f"🚨 ALERT: Failure Detected for {student_name} (Roll: {roll_no})"
                # Here you would trigger: CompartExamRecord.objects.create(...)
            else:
                message = f"✅ Success: {student_name} has passed all requirements."

            return JsonResponse({
                'status': status,
                'message': message,
                'extracted_data': {
                    'name': student_name,
                    'roll': roll_no,
                    'gpa': gpa_value,
                    'failed_subjects': failed_courses
                },
                'raw_text': text
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
def import_records_view(request):
    # This MUST point to the new HTML file we created
    return render(request, 'students/import_records.html')