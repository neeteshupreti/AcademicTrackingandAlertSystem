from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CompartDeadline

def set_deadline(request):
    if request.method == "POST":
        # Pro-level: Handling the specific fields in your model
        cycle = request.POST.get('cycle_name')
        deadline = request.POST.get('form_deadline')
        alert = request.POST.get('alert_date')
        semester = request.POST.get('semester')

        CompartDeadline.objects.create(
            cycle_name=cycle,
            form_deadline=deadline,
            alert_date=alert,
            semester_affected=semester
        )
        messages.success(request, f"Deadline for {cycle} set successfully!")
        return redirect('home')
    
    # Fixed: Using 'form_deadline' for sorting
    deadlines = CompartDeadline.objects.all().order_by('form_deadline')
    return render(request, 'notifications/set_deadline.html', {'deadlines': deadlines})