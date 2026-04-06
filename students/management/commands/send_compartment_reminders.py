"""
Management command to send compartment exam deadline reminders
Usage: python manage.py send_compartment_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from students.models import CompartExamRecord
from students.email_notifications import send_compartment_deadline_reminder
from notifications.models import CompartDeadline


class Command(BaseCommand):
    help = 'Send email reminders to students about upcoming compartment exams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Send reminders X days before deadline (default: 7)',
        )

    def handle(self, *args, **options):
        days_before = options['days']
        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_before)
        
        # Find all compartment records with upcoming deadlines
        try:
            deadlines = CompartDeadline.objects.filter(
                alert_date=reminder_date
            ).select_related('compartment_exam')
            
            if not deadlines.exists():
                self.stdout.write(
                    self.style.WARNING(f'No deadlines found for {reminder_date}')
                )
                return
            
            sent_count = 0
            failed_count = 0
            
            for deadline in deadlines:
                # Get all students in compartment exams
                compart_records = CompartExamRecord.objects.filter(
                    is_cleared=False
                ).select_related('student')
                
                for record in compart_records:
                    if send_compartment_deadline_reminder(record, deadline.alert_date):
                        sent_count += 1
                    else:
                        failed_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Successfully sent {sent_count} reminders\n'
                    f'✗ Failed to send {failed_count} reminders'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
