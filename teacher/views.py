from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from django.db import models
from datetime import date, datetime
from core.models import TeacherProfile, Subject, StudentProfile, Attendance, StudentSubjectEnrollment, Grade

def is_teacher(user):
    return user.is_authenticated and user.is_teacher()

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    """Teacher dashboard with attendance overview"""
    try:
        teacher_profile = request.user.teacher_profile
    except:
        context = {
            'error': 'Teacher profile not found. Please contact administrator.',
            'user': request.user,
            'page_title': 'Teacher Dashboard',
        }
        return render(request, 'dashboards/teacher_dashboard.html', context)
    
    # Get teacher's subjects and attendance overview
    assigned_subjects = teacher_profile.get_assigned_subjects()
    attendance_overview = teacher_profile.get_attendance_overview()
    grading_overview = teacher_profile.get_grading_overview()
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(
        marked_by=teacher_profile
    ).select_related('student__user', 'subject').order_by('-created_at')[:10]
    
    # Get recent grades
    recent_grades = Grade.objects.filter(
        graded_by=teacher_profile
    ).select_related('student__user', 'subject').order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        'teacher_profile': teacher_profile,
        'page_title': 'Teacher Dashboard',
        'assigned_subjects': assigned_subjects,
        'attendance_overview': attendance_overview,
        'grading_overview': grading_overview,
        'recent_attendance': recent_attendance,
        'recent_grades': recent_grades,
        'total_subjects': assigned_subjects.count(),
        'total_students': teacher_profile.get_total_students(),
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def attendance_management(request):
    """Attendance management page for teachers"""
    try:
        teacher_profile = request.user.teacher_profile
    except:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher:teacher_dashboard')
    
    subjects = teacher_profile.get_assigned_subjects()
    selected_subject_id = request.GET.get('subject')
    selected_date = request.GET.get('date', str(date.today()))
    
    context = {
        'user': request.user,
        'teacher_profile': teacher_profile,
        'page_title': 'Attendance Management',
        'subjects': subjects,
        'selected_subject_id': selected_subject_id,
        'selected_date': selected_date,
    }
    
    if selected_subject_id:
        try:
            selected_subject = get_object_or_404(Subject, id=selected_subject_id, teacher=teacher_profile)
            context['selected_subject'] = selected_subject
            
            # Get enrolled students for the subject
            enrolled_students = StudentProfile.objects.filter(
                enrollments__subject=selected_subject,
                enrollments__is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')
            
            # Get existing attendance for the selected date
            attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            existing_attendance = Attendance.objects.filter(
                subject=selected_subject,
                date=attendance_date
            )
            
            attendance_dict = {att.student.id: att for att in existing_attendance}
            
            student_attendance = []
            for student in enrolled_students:
                attendance_record = attendance_dict.get(student.id)
                student_attendance.append({
                    'student': student,
                    'attendance': attendance_record,
                    'status': attendance_record.status if attendance_record else 'absent'
                })
            
            context.update({
                'student_attendance': student_attendance,
                'attendance_date': attendance_date,
                'attendance_already_marked': len(attendance_dict) > 0,
            })
            
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found or not assigned to you.')
    
    return render(request, 'teacher/attendance_management.html', context)

@login_required
@user_passes_test(is_teacher)
def mark_attendance(request):
    """Mark attendance for students"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('teacher:attendance_management')
    
    try:
        teacher_profile = request.user.teacher_profile
        subject_id = request.POST.get('subject_id')
        attendance_date = request.POST.get('date')
        
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        # Get all students enrolled in the subject
        enrolled_students = StudentProfile.objects.filter(
            enrollments__subject=subject,
            enrollments__is_active=True
        )
        
        with transaction.atomic():
            for student in enrolled_students:
                status = request.POST.get(f'attendance_{student.id}', 'absent')
                remarks = request.POST.get(f'remarks_{student.id}', '')
                
                # Update or create attendance record
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    subject=subject,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'remarks': remarks,
                        'marked_by': teacher_profile
                    }
                )
        
        messages.success(request, f'Attendance marked successfully for {subject.name} on {attendance_date}')
        
    except Exception as e:
        messages.error(request, f'Error marking attendance: {str(e)}')
    
    return redirect('teacher:attendance_management')

@login_required
@user_passes_test(is_teacher)
def attendance_reports(request):
    """Generate attendance reports"""
    try:
        teacher_profile = request.user.teacher_profile
    except:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher:teacher_dashboard')
    
    subjects = teacher_profile.get_assigned_subjects()
    selected_subject_id = request.GET.get('subject')
    
    context = {
        'user': request.user,
        'teacher_profile': teacher_profile,
        'page_title': 'Attendance Reports',
        'subjects': subjects,
        'selected_subject_id': selected_subject_id,
    }
    
    if selected_subject_id:
        try:
            selected_subject = get_object_or_404(Subject, id=selected_subject_id, teacher=teacher_profile)
            context['selected_subject'] = selected_subject
            
            # Get attendance statistics
            enrolled_students = StudentProfile.objects.filter(
                enrollments__subject=selected_subject,
                enrollments__is_active=True
            ).select_related('user')
            
            student_stats = []
            for student in enrolled_students:
                total_classes = Attendance.objects.filter(
                    student=student,
                    subject=selected_subject
                ).count()
                
                present_classes = Attendance.objects.filter(
                    student=student,
                    subject=selected_subject,
                    status__in=['present', 'late']
                ).count()
                
                attendance_percentage = round(
                    (present_classes / total_classes * 100), 1
                ) if total_classes > 0 else 0
                
                student_stats.append({
                    'student': student,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': total_classes - present_classes,
                    'attendance_percentage': attendance_percentage
                })
            
            context['student_stats'] = student_stats
            
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found or not assigned to you.')
    
    return render(request, 'teacher/attendance_reports.html', context)

@login_required
@user_passes_test(is_teacher)
def ajax_get_students(request, subject_id):
    """AJAX endpoint to get students for a subject"""
    try:
        teacher_profile = request.user.teacher_profile
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)
        
        enrolled_students = StudentProfile.objects.filter(
            enrollments__subject=subject,
            enrollments__is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        students_data = []
        for student in enrolled_students:
            students_data.append({
                'id': student.id,
                'name': student.user.get_full_name() or student.user.username,
                'student_id': student.student_id
            })
        
        return JsonResponse({
            'success': True,
            'students': students_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
@user_passes_test(is_teacher)
def grade_management(request):
    """Grade management page for teachers"""
    try:
        teacher_profile = request.user.teacher_profile
    except:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher:teacher_dashboard')
    
    subjects = teacher_profile.get_assigned_subjects()
    selected_subject_id = request.GET.get('subject')
    
    context = {
        'user': request.user,
        'teacher_profile': teacher_profile,
        'page_title': 'Grade Management',
        'subjects': subjects,
        'selected_subject_id': selected_subject_id,
    }
    
    if selected_subject_id:
        try:
            selected_subject = get_object_or_404(Subject, id=selected_subject_id, teacher=teacher_profile)
            context['selected_subject'] = selected_subject
            
            # Get enrolled students for the subject
            enrolled_students = StudentProfile.objects.filter(
                enrollments__subject=selected_subject,
                enrollments__is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')
            
            # Get existing grades for the subject
            subject_grades = Grade.objects.filter(
                subject=selected_subject
            ).select_related('student__user').order_by('-date_assigned', 'student__user__first_name')
            
            context.update({
                'enrolled_students': enrolled_students,
                'subject_grades': subject_grades,
            })
            
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found or not assigned to you.')
    
    return render(request, 'teacher/grade_management.html', context)

@login_required
@user_passes_test(is_teacher)
def add_grade(request):
    """Add new grade for students"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('teacher:grade_management')
    
    try:
        teacher_profile = request.user.teacher_profile
        subject_id = request.POST.get('subject_id')
        
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher_profile)
        
        # Get form data
        title = request.POST.get('title')
        grade_type = request.POST.get('grade_type')
        total_marks = request.POST.get('total_marks')
        date_assigned = request.POST.get('date_assigned')
        comments = request.POST.get('comments', '')
        
        with transaction.atomic():
            # Get enrolled students
            enrolled_students = StudentProfile.objects.filter(
                enrollments__subject=subject,
                enrollments__is_active=True
            )
            
            for student in enrolled_students:
                marks_obtained = request.POST.get(f'marks_{student.id}')
                if marks_obtained:  # Only create grade if marks are provided
                    Grade.objects.create(
                        student=student,
                        subject=subject,
                        title=title,
                        grade_type=grade_type,
                        marks_obtained=marks_obtained,
                        total_marks=total_marks,
                        date_assigned=date_assigned,
                        comments=comments,
                        graded_by=teacher_profile,
                        is_published=True  # Auto-publish
                    )
        
        messages.success(request, f'Grades added successfully for {subject.name}')
        
    except Exception as e:
        messages.error(request, f'Error adding grades: {str(e)}')
    
    return redirect('teacher:grade_management')

@login_required
@user_passes_test(is_teacher)
def grade_reports(request):
    """Generate grade reports"""
    try:
        teacher_profile = request.user.teacher_profile
    except:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher:teacher_dashboard')
    
    subjects = teacher_profile.get_assigned_subjects()
    selected_subject_id = request.GET.get('subject')
    
    context = {
        'user': request.user,
        'teacher_profile': teacher_profile,
        'page_title': 'Grade Reports',
        'subjects': subjects,
        'selected_subject_id': selected_subject_id,
    }
    
    if selected_subject_id:
        try:
            selected_subject = get_object_or_404(Subject, id=selected_subject_id, teacher=teacher_profile)
            context['selected_subject'] = selected_subject
            
            # Get grade statistics
            enrolled_students = StudentProfile.objects.filter(
                enrollments__subject=selected_subject,
                enrollments__is_active=True
            ).select_related('user')
            
            student_stats = []
            for student in enrolled_students:
                student_grades = Grade.objects.filter(
                    student=student,
                    subject=selected_subject,
                    is_published=True
                )
                
                if student_grades.exists():
                    total_grades = student_grades.count()
                    avg_percentage = student_grades.aggregate(
                        avg=models.Avg('percentage')
                    )['avg']
                    
                    student_stats.append({
                        'student': student,
                        'total_grades': total_grades,
                        'average_percentage': round(avg_percentage, 1) if avg_percentage else 0,
                        'latest_grade': student_grades.order_by('-date_assigned').first(),
                        'grades': student_grades.order_by('-date_assigned')
                    })
            
            context['student_stats'] = student_stats
            
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found or not assigned to you.')
    
    return render(request, 'teacher/grade_reports.html', context)

@login_required
@user_passes_test(is_teacher)
def edit_grade(request, grade_id):
    """Edit existing grade"""
    try:
        teacher_profile = request.user.teacher_profile
        grade = get_object_or_404(Grade, id=grade_id, graded_by=teacher_profile)
        
        if request.method == 'POST':
            grade.title = request.POST.get('title', grade.title)
            grade.grade_type = request.POST.get('grade_type', grade.grade_type)
            grade.marks_obtained = request.POST.get('marks_obtained', grade.marks_obtained)
            grade.total_marks = request.POST.get('total_marks', grade.total_marks)
            grade.date_assigned = request.POST.get('date_assigned', grade.date_assigned)
            grade.comments = request.POST.get('comments', grade.comments)
            grade.is_published = request.POST.get('is_published') == 'on'
            
            grade.save()
            messages.success(request, 'Grade updated successfully.')
            return redirect('teacher:grade_management')
        
        context = {
            'user': request.user,
            'teacher_profile': teacher_profile,
            'page_title': 'Edit Grade',
            'grade': grade,
        }
        return render(request, 'teacher/edit_grade.html', context)
        
    except Exception as e:
        messages.error(request, f'Error editing grade: {str(e)}')
        return redirect('teacher:grade_management')
