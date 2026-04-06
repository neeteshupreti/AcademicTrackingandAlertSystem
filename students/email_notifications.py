"""
Email notification utilities for student alerts
"""
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Student, CompartExamRecord

logger = logging.getLogger(__name__)


def send_failure_notification(student, gpa, failed_subjects):
    """
    Send email notification to student when they're marked as failed
    
    Args:
        student: Student object
        gpa: Student's GPA (float or string)
        failed_subjects: Comma-separated string of failed subject codes
    """
    if not student.email:
        return False
    
    try:
        subject = "Academic Alert: Review Your Exam Results"
        
        # Parse failed subjects
        subjects_list = [s.strip() for s in failed_subjects.split(",") if s.strip()]
        
        # Email context
        context = {
            'student_name': student.name,
            'gpa': gpa,
            'failed_subjects': subjects_list,
            'student_id': student.registration_number,
            'institution_name': 'University Name',  # Change to actual institution
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/failure_alert.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent to {student.email} for {student.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {student.email}: {str(e)}")
        return False


def send_compartment_deadline_reminder(compartment_record, deadline_date):
    """
    Send compartment exam deadline reminder to student
    
    Args:
        compartment_record: CompartExamRecord object
        deadline_date: Datetime object with exam deadline
    """
    student = compartment_record.student
    if not student.email:
        return False
    
    try:
        subject = f"Compartment Exam Reminder: {compartment_record.subject_name}"
        
        context = {
            'student_name': student.name,
            'subject_name': compartment_record.subject_name,
            'subject_code': compartment_record.subject_code,
            'deadline_date': deadline_date.strftime("%d %B %Y"),
            'deadline_time': deadline_date.strftime("%I:%M %p"),
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_message = render_to_string('emails/compartment_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Compartment reminder sent to {student.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send compartment reminder to {student.email}: {str(e)}")
        return False


def send_bulk_failure_alerts(students_data):
    """
    Send failure alerts to multiple students
    Useful for batch imports
    
    Args:
        students_data: List of tuples (student_obj, gpa, failed_subjects_str)
    """
    success_count = 0
    failed_count = 0
    
    for student, gpa, failed_subjects in students_data:
        if send_failure_notification(student, gpa, failed_subjects):
            success_count += 1
        else:
            failed_count += 1
    
    return {
        'success': success_count,
        'failed': failed_count,
        'total': success_count + failed_count
    }


def send_registration_deadline_notification(compartment_record):
    """
    Send compartment registration deadline notification to student
    
    Args:
        compartment_record: CompartExamRecord object with registration_deadline set
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    student = compartment_record.student
    if not student.email or not compartment_record.registration_deadline:
        return False
    
    try:
        subject = f"Important: Compartment Registration Deadline for {compartment_record.subject_code}"
        
        context = {
            'student_name': student.name,
            'subject_code': compartment_record.subject_code,
            'subject_name': compartment_record.subject_name or 'N/A',
            'student_id': student.registration_number,
            'registration_deadline': compartment_record.registration_deadline.strftime("%d %B %Y"),
            'registration_time': compartment_record.registration_deadline.strftime("%I:%M %p"),
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'current_year': __import__('datetime').date.today().year,
        }
        
        html_message = render_to_string('emails/registration_deadline.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Registration deadline notification sent to {student.email} for {student.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send registration deadline notification to {student.email}: {str(e)}")
        return False


def send_exam_date_notification(compartment_record):
    """
    Send compartment exam date notification to student
    
    Args:
        compartment_record: CompartExamRecord object with exam_date set
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    student = compartment_record.student
    if not student.email or not compartment_record.exam_date:
        return False
    
    try:
        subject = f"Exam Date: Compartment Examination for {compartment_record.subject_code}"
        
        context = {
            'student_name': student.name,
            'subject_code': compartment_record.subject_code,
            'subject_name': compartment_record.subject_name or 'N/A',
            'student_id': student.registration_number,
            'exam_date': compartment_record.exam_date.strftime("%d %B %Y"),
            'exam_time': compartment_record.exam_date.strftime("%I:%M %p"),
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'current_year': __import__('datetime').date.today().year,
        }
        
        html_message = render_to_string('emails/exam_date_notification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Exam date notification sent to {student.email} for {student.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send exam date notification to {student.email}: {str(e)}")
        return False


def send_bulk_dates_and_notifications(records_data, notification_type='registration'):
    """
    Send bulk notifications for compartment dates
    
    Args:
        records_data: List of CompartExamRecord objects
        notification_type: 'registration' for registration deadline, 'exam' for exam date
    
    Returns:
        dict: Summary of sent/failed notifications
    """
    success_count = 0
    failed_count = 0
    
    for record in records_data:
        if notification_type == 'registration':
            if record.registration_deadline and not record.registration_deadline_notified:
                if send_registration_deadline_notification(record):
                    success_count += 1
                else:
                    failed_count += 1
        elif notification_type == 'exam':
            if record.exam_date and not record.exam_date_notified:
                if send_exam_date_notification(record):
                    success_count += 1
                else:
                    failed_count += 1
    
    return {
        'success': success_count,
        'failed': failed_count,
        'total': success_count + failed_count,
        'type': notification_type
    }

