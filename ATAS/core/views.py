from django.shortcuts import render
from students.models import Student, CompartExamRecord # Note: Removed 'Grade'
from notifications.models import CompartDeadline
from django.db.models import Count, Q
import datetime

def home(request):
    """
    Renders the main dashboard with key metrics.
    """
    today = datetime.date.today()
    
    # 1. Total Students
    total_students = Student.objects.count()
    
    # 2. Students Requiring Compartment (Unresolved 'F' grades)
    compartment_students = Student.objects.filter(
        compart_records__is_cleared=False
    ).distinct().count()

    # 3. Upcoming Deadlines (Deadlines that haven't passed yet)
    active_deadlines = CompartDeadline.objects.filter(
        form_deadline__gte=today
    ).count()

    context = {
        'total_students': total_students,
        'compartment_students': compartment_students,
        'active_deadlines': active_deadlines,
    }
    return render(request, 'core/home.html', context)