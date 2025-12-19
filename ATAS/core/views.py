from django.shortcuts import render
from students.models import Student, CompartExamRecord
from notifications.models import CompartDeadline
from django.utils import timezone

def home(request):
    now = timezone.now()
    
    context = {
        'total_students': Student.objects.count(),
        'compartment_students': CompartExamRecord.objects.filter(is_cleared=False).count(),
        
        # Fixed: Using 'form_deadline' instead of 'deadline_date'
        'active_deadlines': CompartDeadline.objects.filter(form_deadline__gte=now).count(),
        
        # Fixed: Ordering by 'form_deadline'
        'upcoming_deadlines': CompartDeadline.objects.filter(
            form_deadline__gte=now
        ).order_by('form_deadline')[:5],
        
        'recent_flags': CompartExamRecord.objects.select_related('student').order_by('-id')[:5]
    }
    return render(request, 'core/home.html', context)