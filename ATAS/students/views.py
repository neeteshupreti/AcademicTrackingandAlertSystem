import re, base64, json, cv2, csv, difflib, uuid
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from PIL import Image
import pytesseract
from .models import Student, CompartExamRecord

# --- CONSTANTS & HELPERS ---
NOISE_WORDS = {"NAME", "STUDENT", "THE", "OF", "OFTHE", "REGISTRATION", "NO", "NUMBER", "REGD", "ROLL", "DATE", "BIRTH", "GENDER", "STUDENTNAME", "PROVISIONAL", "UNIVERSITY", "SCHOOL", "ENGINEERING", "OFFICE", "CONTROLLER", "ACADEMIC", "RECORD", "BACHELOR", "TECHNOLOGY", "KATHMANDU"}

def get_unique_placeholders(name):
    """Generates unique data to satisfy DB constraints."""
    uid = uuid.uuid4().hex[:6].upper()
    return {
        'email': f"{name.lower().replace(' ', '.')}.{uid}@atas.local",
        'reg': f"REG-{uid}"
    }

# --- OCR LOGIC ---
def get_student_name_advanced(processed_img):
    data = pytesseract.image_to_data(Image.fromarray(processed_img), output_type=pytesseract.Output.DICT)
    
    # Find Y-axis of the name line
    target_y = next((data['top'][i] for i, txt in enumerate(data['text']) if any(x in txt.upper() for x in ["STUDENT", "NAME"])), -1)
    
    if target_y == -1: return "Unknown"

    # Collect and sort words on that line
    row = []
    for i in range(len(data['text'])):
        clean = re.sub(r'[^A-Z]', '', data['text'][i].upper())
        if abs(data['top'][i] - target_y) < 30 and clean not in NOISE_WORDS and len(clean) > 1:
            row.append({'text': clean, 'x': data['left'][i]})
    
    row.sort(key=lambda x: x['x'])
    
    # De-duplicate and Merge
    final_words = []
    for word in [r['text'] for r in row]:
        if not any(word in f or f in word or difflib.SequenceMatcher(None, word, f).ratio() > 0.8 for f in final_words):
            final_words.append(word)
    
    ocr_name = " ".join(final_words).strip()
    
    # Database Autocorrect
    matches = difflib.get_close_matches(ocr_name, Student.objects.values_list('name', flat=True), n=1, cutoff=0.4)
    return matches[0] if matches else ocr_name

# --- VIEWS ---
@csrf_exempt
def process_scan(request):
    if request.method != "POST": return JsonResponse({'status': 'error'})
    try:
        img_data = json.loads(request.body).get('image').split(';base64,')[1]
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        _, processed = cv2.threshold(img, 175, 255, cv2.THRESH_BINARY)
        
        # Data Extraction
        name = get_student_name_advanced(processed)
        raw_text = pytesseract.image_to_string(Image.fromarray(processed), config='--psm 6')
        
        failed = [m.group(1) for l in raw_text.split('\n') if (m := re.search(r'\b([A-Z]{3,4}\s?\d{3})\b', l)) and re.search(r'\b(F|\(F\)|INC)\b', l)]
        gpa = m.group(1) if (m := re.search(r"GPA.*?([0-9\.]+|X)", raw_text, re.IGNORECASE)) else "N/A"

        return JsonResponse({
            'status': 'success',
            'extracted_data': {'name': name, 'gpa': gpa, 'failed_subjects': ", ".join(failed) if failed else "None"},
            'is_failing': gpa == "X" or len(failed) > 0
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def upload_gpa_sheet(request):
    if request.method == "POST":
        csv_file = request.FILES.get('gpa_file')
        try:
            reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
            for row in reader:
                name = row.get('Student Name', '').strip().upper()
                gpa_str = row.get('GPA', '0.0').strip().upper()
                
                if name:
                    extra = get_unique_placeholders(name)
                    student, _ = Student.objects.get_or_create(name=name, defaults={'semester': 1, 'email': extra['email'], 'registration_number': extra['reg']})
                    
                    if hasattr(student, 'gpa'):
                        student.gpa = 0.0 if gpa_str == "X" else float(gpa_str)
                        student.save()

                    if gpa_str == "X" or row.get('Failed_Subjects', '').lower() != "none":
                        CompartExamRecord.objects.get_or_create(student=student, subject_name=f"Alert: {row.get('Failed_Subjects', 'Low GPA')}", defaults={'is_cleared': False})
            messages.success(request, "Import successful.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'students/upload_gpa.html')

@csrf_exempt
def save_verified_data(request):
    if request.method == "POST":
        data = json.loads(request.body)
        extra = get_unique_placeholders(data.get('name', 'UNK'))
        student, _ = Student.objects.get_or_create(name=data.get('name').upper(), defaults={'semester': 1, 'registration_number': extra['reg'], 'email': extra['email']})
        if data.get('is_failing'):
            CompartExamRecord.objects.get_or_create(student=student, subject_name=f"Verified: {data.get('failed_subjects')}", defaults={'is_cleared': False})
        return JsonResponse({'status': 'success'})

def compartment_students_list(request):
    return render(request, 'students/list.html', {'records': CompartExamRecord.objects.filter(is_cleared=False).select_related('student')})

def import_records_view(request): return render(request, 'students/import_records.html')