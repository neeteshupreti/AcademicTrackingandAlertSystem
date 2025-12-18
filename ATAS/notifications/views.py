from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import CompartDeadline
from .forms import CompartDeadlineForm

@require_http_methods(["GET", "POST"])
def set_deadline(request):
    """Handles setting new deadlines and displays all existing deadlines."""
    if request.method == 'POST':
        form = CompartDeadlineForm(request.POST)
        if form.is_valid():
            # The save method in the model automatically calculates the alert_date
            form.save() 
            messages.success(request, f"Deadline for '{form.cleaned_data['cycle_name']}' set successfully. Notification scheduled.")
            return redirect('set_deadline')
    else:
        form = CompartDeadlineForm()
    
    # Retrieve all scheduled deadlines, ordered by the deadline date
    deadlines = CompartDeadline.objects.all().order_by('form_deadline')
    
    context = {
        'form': form,
        'deadlines': deadlines,
        'page_title': 'Set & Manage Exam Deadlines'
    }
    return render(request, 'notifications/set_deadline.html', context)