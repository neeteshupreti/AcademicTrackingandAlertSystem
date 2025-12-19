import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Student, CompartExamRecord

def upload_gpa_sheet(request):
    if request.method == "POST" and request.FILES.get('gpa_file'):
        file = request.FILES['gpa_file']
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)

            with transaction.atomic():
                for _, row in df.iterrows():
                    student, _ = Student.objects.update_or_create(
                        student_id=row['student_id'],
                        defaults={'name': row['name'], 'gpa': row['gpa']}
                    )

                    if row['gpa'] < 2.0:
                        # Fixed: Use 'subject_name' and 'is_cleared' per your model
                        CompartExamRecord.objects.update_or_create(
                            student=student,
                            subject_name=row.get('subject', 'General'), 
                            defaults={
                                'is_cleared': False,
                                'grade': row['gpa']
                            }
                        )
            messages.success(request, "Data processed successfully!")
            return redirect('compartment_students')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return render(request, 'students/upload_gpa.html')

def compartment_students_list(request):
    # Fixed: Passing 'records' to the template
    records = CompartExamRecord.objects.select_related('student').all()
    return render(request, 'students/compartment_list.html', {'records': records})