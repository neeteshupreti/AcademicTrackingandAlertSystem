import re, base64, json, cv2, csv, uuid
import logging
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from PIL import Image
import pytesseract
from .models import Student, CompartExamRecord, CompartExamConfig
from .email_notifications import send_failure_notification
from .ocr_utils import parse_ku_report, extract_ocr_data_from_image, get_student_name_from_ocr_data

logger = logging.getLogger(__name__)

# --- CONSTANTS & HELPERS ---
def get_unique_placeholders(name):
    """Generates unique data to satisfy DB constraints."""
    uid = uuid.uuid4().hex[:6].upper()
    return {
        'email': f"{name.lower().replace(' ', '.')}.{uid}@atas.local",
        'reg': f"REG-{uid}"
    }


# --- IMAGE PREPROCESSING (Not used - raw images work better with PSM 6) ---
# Keeping these functions for potential future use but not active
def preprocess_ocr_image(img_gray):
    """
    DEPRECATED: Not used - table structure is destroyed by preprocessing.
    PSM 6 configuration works better on raw images for grade extraction.
    """
    pass

# --- VIEWS ---
@csrf_exempt
def process_scan(request):
    """
    Process an uploaded GPA sheet image (KU format).
    Extracts: name, registration number, semester, GPA, and failed subjects.
    """
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'POST request required'})
    
    try:
        # Decode image from base64
        img_data = json.loads(request.body).get('image').split(';base64,')[1]
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        # Use PSM 4 for mixed layouts - better preserves tables with courses
        # PSM 4 handles mixed layouts of text and tables
        raw_text = pytesseract.image_to_string(
            img, 
            config='--psm 4 --oem 3 -l eng'
        )
        
        logger.info(f"OCR extracted {len(raw_text)} characters from image")
        
        # Get database student names for fuzzy matching
        db_student_names = list(Student.objects.values_list('name', flat=True).distinct())
        
        # Parse using improved KU report parser with enhanced extraction
        parsed_data = parse_ku_report(raw_text, img, db_student_names=db_student_names)

        return JsonResponse({
            'status': 'success',
            'extracted_data': {
                'name': parsed_data['name'],
                'registration_no': parsed_data.get('registration_no'),
                'year': parsed_data.get('year', 1),
                'semester': parsed_data['semester'],
                'gpa': parsed_data['gpa'],
                'failed_subjects': ", ".join(parsed_data['failed_subjects']) if parsed_data['failed_subjects'] else "None"
            },
            'is_failing': parsed_data['is_failing'],
            'confidence': parsed_data['extraction_confidence'],
            'raw_text': raw_text  # Include for debugging/verification
        })
    except Exception as e:
        logger.error(f"Error processing scan: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def upload_gpa_sheet(request):
    """
    Upload and process GPA sheet CSV file.
    Expected CSV columns: Student Name, GPA, Failed_Subjects, Year, Semester (optional)
    """
    if request.method == "POST":
        csv_file = request.FILES.get('gpa_file')
        try:
            reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
            email_stats = {'sent': 0, 'failed': 0}
            
            for row in reader:
                name = row.get('Student Name', '').strip()
                gpa_str = row.get('GPA', '0.0').strip().upper()
                failed_subjects_str = row.get('Failed_Subjects', 'none').strip()
                year = int(row.get('Year', 1))
                semester = int(row.get('Semester', 1))
                
                if name:
                    extra = get_unique_placeholders(name)
                    student, created = Student.objects.get_or_create(
                        name=name,
                        defaults={
                            'current_year': year,
                            'current_semester': semester,
                            'email': extra['email'],
                            'registration_number': extra['reg']
                        }
                    )
                    
                    # Update year and semester if existing student
                    if not created:
                        if student.current_year < year:
                            student.current_year = year
                        if student.current_semester < semester:
                            student.current_semester = semester
                        student.save()
                    
                    # Update GPA
                    if gpa_str != "X":
                        try:
                            student.gpa = float(gpa_str) if gpa_str != "none" else 0.0
                        except ValueError:
                            student.gpa = 0.0
                    student.save()

                    # Process failed subjects
                    if gpa_str == "X" or failed_subjects_str.lower() != "none":
                        for subject_code in failed_subjects_str.split(","):
                            subject_code = subject_code.strip()
                            if subject_code:
                                # Get subject name from CompartExamConfig, if available
                                subject_name = subject_code
                                try:
                                    config = CompartExamConfig.objects.get(subject_code=subject_code)
                                    if config.subject_name:
                                        subject_name = config.subject_name
                                except CompartExamConfig.DoesNotExist:
                                    pass
                                
                                CompartExamRecord.objects.get_or_create(
                                    student=student,
                                    subject_code=subject_code,
                                    year=year,
                                    semester=semester,
                                    defaults={
                                        'grade': 'F',
                                        'gpa_at_failure': student.gpa,
                                        'is_cleared': False,
                                        'subject_name': subject_name
                                    }
                                )
                        
                        # Send email notification
                        if send_failure_notification(student, gpa_str, failed_subjects_str):
                            email_stats['sent'] += 1
                        else:
                            email_stats['failed'] += 1
            
            message_text = f"Import successful. Emails sent: {email_stats['sent']}, Failed: {email_stats['failed']}"
            messages.success(request, message_text)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'students/upload_gpa.html')

@csrf_exempt
def save_verified_data(request):
    """
    Save verified data from OCR scan.
    Creates/updates student and compartment records with year/semester support.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name', 'UNK').strip()
            registration_no = data.get('registration_no', None)
            gpa = data.get('gpa', None)
            failed_subjects = data.get('failed_subjects', '')
            year = data.get('year', 1)
            semester = data.get('semester', 1)
            is_failing = data.get('is_failing', False)
            
            extra = get_unique_placeholders(name)
            
            # Use extracted registration number if available, otherwise generate
            final_reg_no = registration_no if registration_no else extra['reg']
            
            student, created = Student.objects.get_or_create(
                name=name,
                defaults={
                    'current_year': year,
                    'current_semester': semester,
                    'registration_number': final_reg_no,
                    'email': extra['email']
                }
            )
            
            # Update registration number if it was extracted from report
            if registration_no and student.registration_number != final_reg_no:
                student.registration_number = final_reg_no
            
            # Update year and semester if this is newer data
            if not created:
                if student.current_year < year:
                    student.current_year = year
                if student.current_semester < semester:
                    student.current_semester = semester
            
            # Save GPA if provided and valid
            try:
                if gpa and gpa != "N/A" and gpa != "X":
                    student.gpa = float(gpa)
                elif gpa == "X":
                    student.gpa = 0.0
                student.save()
            except Exception as e:
                logger.error(f"Error saving GPA: {e}")

            # Save failed subjects as compartment records if failing
            if is_failing and failed_subjects and failed_subjects.lower() != "none":
                for subj in failed_subjects.split(","):
                    subject_code = subj.strip()
                    if subject_code:
                        # Get subject name from CompartExamConfig, if available
                        subject_name = subject_code
                        try:
                            config = CompartExamConfig.objects.get(subject_code=subject_code)
                            if config.subject_name:
                                subject_name = config.subject_name
                        except CompartExamConfig.DoesNotExist:
                            pass
                        
                        # Create compartment record with year and semester information
                        compartment_record, created = CompartExamRecord.objects.get_or_create(
                            student=student,
                            subject_code=subject_code,
                            year=year,
                            semester=semester,
                            defaults={
                                'grade': 'F',
                                'gpa_at_failure': student.gpa,
                                'is_cleared': False,
                                'subject_name': subject_name
                            }
                        )
                
                # Send failure notification email to student
                try:
                    send_failure_notification(student, gpa, failed_subjects)
                except Exception as e:
                    logger.error(f"Email notification failed: {e}")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Student {name} (Year {year}, Semester {semester}) saved successfully'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid JSON: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in save_verified_data", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving record: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'POST request required'})

def compartment_students_list(request):
    """Display list of students with active compartments with search and filters."""
    from django.db.models import Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Base queryset - only active (not cleared) records
    records = CompartExamRecord.objects.filter(
        is_cleared=False
    ).select_related('student').distinct()
    
    # Get unique values for filters
    all_semesters = sorted(set(
        CompartExamRecord.objects.filter(is_cleared=False).values_list('semester', flat=True)
    ))
    all_years = sorted(set(
        CompartExamRecord.objects.filter(is_cleared=False).values_list('year', flat=True)
    ), reverse=True)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        records = records.filter(
            Q(student__name__icontains=search_query) |
            Q(student__registration_number__icontains=search_query) |
            Q(student__email__icontains=search_query) |
            Q(subject_code__icontains=search_query)
        )
    
    # Semester filter
    semester_filter = request.GET.get('semester', '').strip()
    if semester_filter:
        try:
            records = records.filter(semester=int(semester_filter))
        except (ValueError, TypeError):
            pass
    
    # Year filter
    year_filter = request.GET.get('year', '').strip()
    if year_filter:
        try:
            records = records.filter(year=int(year_filter))
        except (ValueError, TypeError):
            pass
    
    # Status filter
    status_filter = request.GET.get('status', '').strip()
    now = timezone.now()
    
    if status_filter == 'alerted_failing':
        # Records that already have failing alerts sent
        records = records.filter(registration_deadline_notified=True)
    elif status_filter == 'alerted_registration':
        # Records alerted for registration deadline
        records = records.filter(
            registration_deadline__isnull=False,
            registration_deadline_notified=True
        )
    elif status_filter == 'alerted_exam':
        # Records alerted for exam date
        records = records.filter(
            exam_date__isnull=False,
            exam_date_notified=True
        )
    elif status_filter == 'exam_passed':
        # Records where exam has passed (past exam date but not cleared)
        records = records.filter(
            exam_date__isnull=False,
            exam_date__lt=now,
            is_cleared=False
        )
    elif status_filter == 'pending_exam':
        # Records where exam is still upcoming
        records = records.filter(
            exam_date__isnull=False,
            exam_date__gte=now,
            is_cleared=False
        )
    
    # Order by year and semester
    records = records.order_by('-year', '-semester', 'student__name')
    
    context = {
        'records': records,
        'show_semester': True,
        'search_query': search_query,
        'selected_semester': semester_filter,
        'selected_year': year_filter,
        'selected_status': status_filter,
        'all_semesters': all_semesters,
        'all_years': all_years,
        'now': now,
    }
    
    return render(request, 'students/list.html', context)

def import_records_view(request):
    """Display import records form."""
    return render(request, 'students/import_records.html')

def get_record_detail(request, record_id):
    """
    API endpoint to fetch detailed information about a compartment record.
    Used by dashboard and student list modals.
    """
    from django.utils import timezone
    
    try:
        record = CompartExamRecord.objects.select_related('student').get(id=record_id)
        now = timezone.now()
        
        # Determine current status
        if record.is_cleared:
            status = 'cleared'
            status_display = 'Exam Cleared'
        elif record.exam_date and record.exam_date < now:
            status = 'exam_passed'
            status_display = 'Exam Passed (Result Pending)'
        elif record.exam_date and record.exam_date > now:
            if record.exam_date_notified:
                status = 'exam_scheduled'
                status_display = 'Exam Scheduled & Notified'
            else:
                status = 'exam_scheduled'
                status_display = 'Exam Scheduled'
        elif record.registration_deadline and record.registration_deadline > now:
            if record.registration_deadline_notified:
                status = 'registration_pending'
                status_display = 'Registration Deadline Notified'
            else:
                status = 'registration_pending'
                status_display = 'Awaiting Registration'
        else:
            status = 'pending_alert'
            status_display = 'Pending Alert'
        
        # Calculate days until important dates
        days_to_registration = None
        days_to_exam = None
        
        if record.registration_deadline:
            days_to_registration = (record.registration_deadline - now).days
        if record.exam_date:
            days_to_exam = (record.exam_date - now).days
        
        return JsonResponse({
            'status': 'success',
            'record': {
                'id': record.id,
                'student_name': record.student.name,
                'registration_number': record.student.registration_number,
                'student_email': record.student.email,
                'student_gpa': record.student.gpa,
                'subject_code': record.subject_code,
                'subject_name': record.subject_name or 'N/A',
                'grade': record.grade,
                'year': record.year,
                'semester': record.semester,
                'gpa_at_failure': record.gpa_at_failure or 'N/A',
                'status': status,
                'status_display': status_display,
                'is_cleared': record.is_cleared,
                'registration_deadline': record.registration_deadline.isoformat() if record.registration_deadline else None,
                'exam_date': record.exam_date.isoformat() if record.exam_date else None,
                'registration_deadline_notified': record.registration_deadline_notified,
                'exam_date_notified': record.exam_date_notified,
                'days_to_registration': days_to_registration,
                'days_to_exam': days_to_exam,
                'date_created': record.date_created.isoformat(),
            }
        })
    except CompartExamRecord.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Record not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error fetching record detail: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Error fetching record: {str(e)}'
        }, status=500)