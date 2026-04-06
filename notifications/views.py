from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import CompartDeadline, Course, Faculty
from .forms import CompartDeadlineForm, BulkAlertForm, QuickAlertForm
from students.models import Student, CompartExamRecord
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def get_students_by_year_semester(request):
    """
    AJAX endpoint to get students filtered by year and semester.
    """
    year = request.GET.get('year', '')
    semester = request.GET.get('semester', '')
    
    students = Student.objects.filter(is_active=True)
    
    if year:
        try:
            year = int(year)
            students = students.filter(current_year=year)
        except (ValueError, TypeError):
            pass
    
    if semester:
        try:
            semester = int(semester)
            students = students.filter(current_semester=semester)
        except (ValueError, TypeError):
            pass
    
    students = students.order_by('name')
    
    return JsonResponse({
        'status': 'success',
        'students': [
            {
                'id': s.id,
                'name': s.name,
                'registration_number': s.registration_number,
                'current_year': s.current_year,
                'current_semester': s.current_semester,
            }
            for s in students
        ]
    })


def set_deadline(request):
    if request.method == "POST":
        # Get IDs from the dropdowns
        course_id = request.POST.get('course')
        faculty_id = request.POST.get('faculty')
        
        CompartDeadline.objects.create(
            cycle_name=request.POST.get('cycle_name'),
            course_id=course_id,
            assigned_faculty_id=faculty_id,
            semester_affected=request.POST.get('semester'),
            form_deadline=request.POST.get('form_deadline'),
            alert_date=request.POST.get('alert_date')
        )
        messages.success(request, "Deadline scheduled and linked to Faculty!")
        return redirect('home')
    
    context = {
        'deadlines': CompartDeadline.objects.all().order_by('form_deadline'),
        'courses': Course.objects.all(),
        'faculties': Faculty.objects.all()
    }
    return render(request, 'notifications/set_deadline.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def send_bulk_alerts(request):
    """
    View for sending alerts to multiple students about specific subjects.
    Supports three types of alerts:
    - Failing Record Alerts
    - Compartment Registration Deadline Alerts
    - Compartment Exam Date Alerts
    """
    
    if request.method == 'POST':
        form = BulkAlertForm(request.POST)
        
        if form.is_valid():
            students = form.cleaned_data['students']
            subjects = form.cleaned_data['subjects']  # List of subject codes
            alert_type = form.cleaned_data['alert_type']
            custom_message = form.cleaned_data.get('custom_message', '').strip()
            send_test = form.cleaned_data.get('send_test', False)
            
            # Prepare alert data
            alert_data = {
                'alert_type': alert_type,
                'students': students,
                'subjects': subjects,
                'custom_message': custom_message,
            }
            
            # Send test email if requested
            if send_test and request.user.email:
                try:
                    send_test_alert(request.user.email, alert_data)
                    messages.success(request, f"✓ Test email sent to {request.user.email}")
                except Exception as e:
                    messages.error(request, f"✗ Failed to send test email: {str(e)}")
                    logger.error(f"Test email failed: {str(e)}")
            
            # Send actual alerts
            try:
                sent_count = send_alerts_to_students(students, alert_data)
                messages.success(
                    request,
                    f"✓ Successfully sent {sent_count} alert(s) to {len(students)} student(s)"
                )
                logger.info(f"Bulk alert sent: type={alert_type}, students={len(students)}, subjects={subjects}")
                
                return redirect('send_bulk_alerts')
            
            except Exception as e:
                messages.error(request, f"✗ Error sending alerts: {str(e)}")
                logger.error(f"Bulk alert failed: {str(e)}")
    
    else:
        form = BulkAlertForm()
    
    # Get statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_failed_subjects = CompartExamRecord.objects.filter(
        is_cleared=False
    ).values('subject_code').distinct().count()
    
    context = {
        'form': form,
        'total_students': total_students,
        'total_failed_subjects': total_failed_subjects,
        'title': 'Send Bulk Alerts',
    }
    
    return render(request, 'notifications/send_bulk_alerts.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def send_quick_alert(request):
    """
    Quick alert sender for immediate notifications to students.
    """
    
    if request.method == 'POST':
        form = QuickAlertForm(request.POST)
        
        if form.is_valid():
            students = form.cleaned_data['students']
            subject = form.cleaned_data.get('subject', '').strip()
            message = form.cleaned_data['message']
            additional_emails = form.cleaned_data.get('email_recipients', [])
            
            try:
                sent_count = 0
                
                # Send to selected students
                for student in students:
                    if student.email:
                        send_quick_alert_email(
                            student.email,
                            student.name,
                            subject,
                            message
                        )
                        sent_count += 1
                
                # Send to additional recipients
                for email in additional_emails:
                    send_quick_alert_email(
                        email,
                        email,
                        subject,
                        message
                    )
                    sent_count += 1
                
                messages.success(
                    request,
                    f"✓ Alert sent to {sent_count} recipient(s)"
                )
                logger.info(f"Quick alert sent: students={len(students)}, subject={subject}")
                
                return redirect('send_quick_alert')
            
            except Exception as e:
                messages.error(request, f"✗ Error sending alert: {str(e)}")
                logger.error(f"Quick alert failed: {str(e)}")
    
    else:
        form = QuickAlertForm()
    
    context = {
        'form': form,
        'title': 'Send Quick Alert',
    }
    
    return render(request, 'notifications/send_quick_alert.html', context)


def send_alerts_to_students(students, alert_data):
    """
    Send alerts to multiple students based on type.
    
    Args:
        students: QuerySet of Student objects
        alert_data: Dict with alert_type, subjects, custom_message
    
    Returns:
        Number of alerts sent
    """
    alert_type = alert_data['alert_type']
    subjects = alert_data['subjects']
    custom_message = alert_data.get('custom_message', '')
    
    # Parse subjects string into a list (comma-separated)
    subject_list = []
    if subjects and isinstance(subjects, str):
        subject_list = [s.strip() for s in subjects.split(',') if s.strip()]
    
    sent_count = 0
    
    for student in students:
        if not student.email:
            continue
        
        # Get relevant subjects for this student
        if alert_type == 'failing_record':
            # Get all failed subjects for this student
            failed_records = CompartExamRecord.objects.filter(
                student=student,
                is_cleared=False
            )
            
            # Filter by specific subjects if provided
            if subject_list:
                failed_records = failed_records.filter(
                    subject_code__in=subject_list
                )
            
            if failed_records.exists():
                try:
                    send_failing_record_alert(student, failed_records, custom_message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send alert to {student.email}: {str(e)}")
        
        elif alert_type == 'compart_registration':
            # Get registration deadline info for subjects
            deadline_records = CompartExamRecord.objects.filter(
                student=student,
                registration_deadline__isnull=False,
                is_cleared=False
            )
            
            if subject_list:
                deadline_records = deadline_records.filter(
                    subject_code__in=subject_list
                )
            
            if deadline_records.exists():
                try:
                    send_registration_deadline_alert(student, deadline_records, custom_message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send alert to {student.email}: {str(e)}")
        
        elif alert_type == 'compart_exam':
            # Get exam date info for subjects
            exam_records = CompartExamRecord.objects.filter(
                student=student,
                exam_date__isnull=False,
                is_cleared=False
            )
            
            if subject_list:
                exam_records = exam_records.filter(
                    subject_code__in=subject_list
                )
            
            if exam_records.exists():
                try:
                    send_exam_date_alert(student, exam_records, custom_message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send alert to {student.email}: {str(e)}")
    
    return sent_count


def send_test_alert(email, alert_data):
    """Send a test alert to verify configuration"""
    subject = "Test Alert - ATAS Compartment Management System"
    message = f"""
    This is a test alert from the ATAS Compartment Management System.
    
    Alert Type: {alert_data['alert_type']}
    
    If you received this, the alert system is working correctly.
    
    ---
    ATAS - Academic Tracking and Alert System
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_failing_record_alert(student, failed_records, custom_message=''):
    """Send alert about failed subjects"""
    
    subject = f"Alert: Failed Subjects - {student.name}"
    
    context = {
        'student_name': student.name,
        'student_id': student.registration_number,
        'failed_subjects': [
            {
                'code': r.subject_code,
                'name': r.subject_name or 'N/A',
                'year': r.year,
                'semester': r.semester,
                'grade': r.grade,
            }
            for r in failed_records
        ],
        'custom_message': custom_message,
    }
    
    html_message = render_to_string('notifications/email/failing_record_alert.html', context)
    
    send_mail(
        subject,
        f"You have failed subjects. Please check the attached report.",
        settings.DEFAULT_FROM_EMAIL,
        [student.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_registration_deadline_alert(student, deadline_records, custom_message=''):
    """Send alert about compartment registration deadline"""
    
    subject = f"Alert: Compartment Registration Deadline - {student.name}"
    
    context = {
        'student_name': student.name,
        'student_id': student.registration_number,
        'subjects': [
            {
                'code': r.subject_code,
                'name': r.subject_name or 'N/A',
                'deadline': r.registration_deadline,
            }
            for r in deadline_records
        ],
        'custom_message': custom_message,
    }
    
    html_message = render_to_string('notifications/email/registration_deadline_alert.html', context)
    
    send_mail(
        subject,
        f"Compartment registration deadline approaching.",
        settings.DEFAULT_FROM_EMAIL,
        [student.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_exam_date_alert(student, exam_records, custom_message=''):
    """Send alert about compartment exam date"""
    
    subject = f"Alert: Compartment Exam Date - {student.name}"
    
    context = {
        'student_name': student.name,
        'student_id': student.registration_number,
        'exams': [
            {
                'code': r.subject_code,
                'name': r.subject_name or 'N/A',
                'exam_date': r.exam_date,
            }
            for r in exam_records
        ],
        'custom_message': custom_message,
    }
    
    html_message = render_to_string('notifications/email/exam_date_alert.html', context)
    
    send_mail(
        subject,
        f"Compartment exam date reminder.",
        settings.DEFAULT_FROM_EMAIL,
        [student.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_quick_alert_email(email, recipient_name, subject_code, message):
    """Send a quick custom alert email"""
    
    subject = f"Alert: {subject_code}" if subject_code else "System Alert"
    
    full_message = f"""
Dear {recipient_name},

{message}

---
ATAS - Academic Tracking and Alert System
"""
    
    send_mail(
        subject,
        full_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )