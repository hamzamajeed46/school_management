from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from core.models import StudentProfile, Subject, StudentSubjectEnrollment

def is_student(user):
    return user.is_authenticated and user.is_student()

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Student dashboard view with enrollment information"""
    try:
        student_profile = request.user.student_profile
    except:
        # If no profile exists, show error message
        context = {
            'error': 'Student profile not found. Please contact administrator.',
            'user': request.user,
            'page_title': 'Student Dashboard',
        }
        return render(request, 'dashboards/student_dashboard.html', context)
    
    # Get enrolled subjects
    enrolled_subjects = student_profile.get_enrolled_subjects()
    
    # Get available subjects for enrollment
    available_subjects = student_profile.get_available_subjects()
    
    # Calculate enrollment statistics
    total_enrolled = student_profile.get_enrollment_count()
    max_subjects = 8  # Maximum allowed subjects
    can_enroll_more = total_enrolled < max_subjects
    
    context = {
        'user': request.user,
        'student_profile': student_profile,
        'page_title': 'Student Dashboard',
        'enrolled_subjects': enrolled_subjects,
        'available_subjects': available_subjects,
        'total_enrolled': total_enrolled,
        'max_subjects': max_subjects,
        'can_enroll_more': can_enroll_more,
        'enrollment_percentage': round((total_enrolled / max_subjects) * 100, 1) if max_subjects > 0 else 0,
    }
    return render(request, 'dashboards/student_dashboard.html', context)

@login_required
@user_passes_test(is_student)
def subject_enrollment(request):
    """Subject enrollment management page"""
    try:
        student_profile = request.user.student_profile
    except:
        messages.error(request, 'Student profile not found. Please contact administrator.')
        return redirect('students:student_dashboard')
    
    enrolled_subjects = student_profile.get_enrolled_subjects()
    available_subjects = student_profile.get_available_subjects()
    
    context = {
        'user': request.user,
        'student_profile': student_profile,
        'page_title': 'Subject Enrollment',
        'enrolled_subjects': enrolled_subjects,
        'available_subjects': available_subjects,
        'max_subjects': 8,
        'current_count': student_profile.get_enrollment_count(),
    }
    return render(request, 'students/subject_enrollment.html', context)

@login_required
@user_passes_test(is_student)
def enroll_subject(request, subject_id):
    """Enroll in a specific subject"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('students:subject_enrollment')
    
    try:
        student_profile = request.user.student_profile
        subject = get_object_or_404(Subject, id=subject_id)
        
        success, message = student_profile.enroll_in_subject(subject)
        
        if success:
            messages.success(request, f'Successfully enrolled in {subject.name}')
        else:
            messages.error(request, f'Failed to enroll: {message}')
            
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('students:subject_enrollment')

@login_required
@user_passes_test(is_student)
def unenroll_subject(request, subject_id):
    """Unenroll from a specific subject"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('students:subject_enrollment')
    
    try:
        student_profile = request.user.student_profile
        subject = get_object_or_404(Subject, id=subject_id)
        
        success, message = student_profile.unenroll_from_subject(subject)
        
        if success:
            messages.success(request, f'Successfully unenrolled from {subject.name}')
        else:
            messages.error(request, f'Failed to unenroll: {message}')
            
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('students:subject_enrollment')

@login_required
@user_passes_test(is_student)
def ajax_enroll_subject(request, subject_id):
    """AJAX endpoint for subject enrollment"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        student_profile = request.user.student_profile
        subject = get_object_or_404(Subject, id=subject_id)
        
        success, message = student_profile.enroll_in_subject(subject)
        
        return JsonResponse({
            'success': success,
            'message': message,
            'enrolled_count': student_profile.get_enrollment_count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
