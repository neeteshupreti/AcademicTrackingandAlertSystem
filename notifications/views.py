from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CompartDeadline, Course, Faculty

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