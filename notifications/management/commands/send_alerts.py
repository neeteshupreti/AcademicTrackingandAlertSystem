import datetime
from django.core.management.base import BaseCommand
from django.db.models import F
from django.template.loader import render_to_string
from django.core.mail import send_mass_mail
from notifications.models import CompartDeadline
from students.models import Student

class Command(BaseCommand):
    help = 'Checks for impending deadlines and sends compartment exam alerts.'

    def handle(self, *args, **options):
        # Set today's date for comparison
        today = datetime.date.today()
        
        # 1. Find all deadlines where the alert date matches today AND alert hasn't been sent
        pending_alerts = CompartDeadline.objects.filter(
            alert_date__exact=today,
            is_alert_sent=False
        )

        if not pending_alerts.exists():
            self.stdout.write(self.style.SUCCESS('No compartment alerts scheduled for today.'))
            return

        for deadline in pending_alerts:
            # 2. Get all students affected by the semester associated with this deadline
            # Only students with UNCLEARED compartments in the specified semester
            affected_students = Student.objects.filter(
                compart_records__is_cleared=False,
                semester=deadline.semester_affected
            ).distinct()
            
            if not affected_students.exists():
                self.stdout.write(self.style.WARNING(f"No affected students found for deadline: {deadline.cycle_name}."))
                # Mark as sent anyway to prevent future runs (or decide not to based on policy)
                deadline.is_alert_sent = True
                deadline.save()
                continue
            
            self.stdout.write(self.style.SUCCESS(f"Preparing to send alerts for {deadline.cycle_name} to {affected_students.count()} students."))

            email_messages = []
            
            # 3. Compile email data for mass sending
            for student in affected_students:
                # Fetch only the UNCLEARED records for the email content
                compart_records = student.compart_records.filter(is_cleared=False)
                
                context = {
                    'student_name': student.name,
                    'reg_no': student.registration_number,
                    'deadline': deadline,
                    'records': compart_records,
                }

                # Render email body from a template (notifications/templates/emails/alert.txt)
                email_body = render_to_string('notifications/emails/alert.txt', context)

                email_messages.append((
                    f"URGENT: Compartment Exam Form Deadline - {deadline.cycle_name}", # Subject
                    email_body, # Message Body
                    'noreply@atas.edu', # From Email (Requires settings.EMAIL_HOST setup)
                    [student.email], # Recipient List
                ))

            # 4. Send Emails
            try:
                # send_mass_mail is efficient for sending many emails at once
                send_mass_mail(tuple(email_messages), fail_silently=False)
                
                # 5. Mark Deadline as Alert Sent
                deadline.is_alert_sent = True
                deadline.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully sent {len(email_messages)} alerts for {deadline.cycle_name}."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error sending emails for {deadline.cycle_name}: {e}"))

# This command should be scheduled to run daily using a cron job or system scheduler.
# Example cron: 0 9 * * * /path/to/venv/bin/python /path/to/manage.py send_alerts