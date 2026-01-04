import re
import base64
import json
import cv2
import numpy as np
import io
import csv
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from PIL import Image
import pytesseract

from .models import Student, CompartExamRecord

# --- 1. OCR SCANNING LOGIC ---
@csrf_exempt
def process_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            img_str = data.get('image').split(';base64,')[1]
            
            # Pre-processing for KU White-Paper Transcripts
            nparr = np.frombuffer(base64.b64decode(img_str), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY)[1]
            
            # OCR Extraction
            raw_text = pytesseract.image_to_string(Image.fromarray(processed), config='--psm 6')
            lines = [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 1]

            # --- NAME EXTRACTION (Elimination Strategy) ---
            student_name = "Unknown"
            noise_words = [
                "UNIVERSITY", "SCHOOL", "ENGINEERING", "OFFICE", "CONTROLLER", 
                "EXAMINATIONS", "GRADE", "SHEET", "PROVISIONAL", "KATHMANDU",
                "ACADEMIC", "RECORD", "OFFICIAL", "TRANSCRIPT", "PROGRAM",
                "SURNAME", "FIRST", "MIDDLE", "NAME", "STUDENT", "REGISTRATION"
            ]

            candidates = []
            for line in lines[:20]: # Check top header section
                clean_line = re.sub(r'[:\.]', '', line).strip()
                # A name is ALL CAPS, 2+ words, and not a university header
                if clean_line.isupper() and len(clean_line.split()) >= 2:
                    if not any(word in clean_line for word in noise_words):
                        candidates.append(clean_line)

            if candidates:
                student_name = candidates[0]

            # --- FAILED SUBJECT LOGIC (Your Working Logic) ---
            failed_list = []
            for line in lines:
                course_match = re.search(r'\b([A-Z]{3,4}\s?\d{3})\b', line)
                if course_match:
                    # Looking for (F), F, or INC marks
                    if re.search(r'\b(F|\(F\)|INC)\b', line):
                        failed_list.append(course_match.group(1))

            # --- GPA STATUS ---
            gpa_val = "N/A"
            gpa_match = re.search(r"GPA.*?([0-9\.]+|X)", raw_text, re.IGNORECASE)
            if gpa_match:
                gpa_val = gpa_match.group(1)

            is_failing = (gpa_val == "X") or (len(failed_list) > 0)
            
            return JsonResponse({
                'status': 'success',
                'is_failing': is_failing,
                'extracted_data': {
                    'name': student_name, 
                    'gpa': gpa_val,
                    'failed_subjects': ", ".join(failed_list) if failed_list else "None"
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# --- 2. DATABASE PERSISTENCE ---
@csrf_exempt
def save_verified_data(request):
    """Saves the individual OCR results verified by the user."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name', 'Unknown').strip().upper()
            gpa = data.get('gpa')
            failed_subj = data.get('failed_subjects', '')
            
            # Update Student Profile
            student, _ = Student.objects.update_or_create(
                name=name,
                defaults={'gpa': 0.0 if gpa == "X" else (float(gpa) if str(gpa).replace('.','',1).isdigit() else 0.0)}
            )
            
            # Create Backlog Record if failing
            if data.get('is_failing'):
                CompartExamRecord.objects.get_or_create(
                    student=student, 
                    subject_name=f"Failed: {failed_subj}",
                    defaults={'is_cleared': False}
                )
            return JsonResponse({'status': 'success', 'message': f'Record for {name} saved.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# --- 3. CSV BULK IMPORT LOGIC ---
def upload_gpa_sheet(request):
    """Handles CSV/Excel uploads for mass student records."""
    if request.method == "POST":
        csv_file = request.FILES.get('gpa_file')
        
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Error: Please upload a valid .csv file.')
            return render(request, 'students/upload_gpa.html')

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            count = 0
            for row in reader:
                # Column names must match: 'Student Name', 'GPA', 'Failed_Subjects'
                name = row.get('Student Name', '').strip().upper()
                gpa = row.get('GPA', '0.0')
                failed = row.get('Failed_Subjects', '')

                if name:
                    student, _ = Student.objects.update_or_create(
                        name=name,
                        defaults={'gpa': 0.0 if gpa == "X" else float(gpa)}
                    )

                    # Trigger alert record if GPA is X or failed subjects exist
                    if gpa == "X" or (failed and failed.lower() != "none"):
                        CompartExamRecord.objects.get_or_create(
                            student=student,
                            subject_name=f"Backlog: {failed}",
                            defaults={'is_cleared': False}
                        )
                    count += 1
            
            messages.success(request, f'ATAS Update: Successfully imported {count} records.')
        except Exception as e:
            messages.error(request, f'System Error: {str(e)}')

    return render(request, 'students/upload_gpa.html')

# --- 4. VIEW RENDERING ---
def import_records_view(request):
    """Renders the Image/Webcam OCR Scanner page."""
    return render(request, 'students/import_records.html')

def compartment_students_list(request):
    """Renders the list of students flagged by the system."""
    records = CompartExamRecord.objects.select_related('student').filter(is_cleared=False)
    return render(request, 'students/list.html', {'records': records})