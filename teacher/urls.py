from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    # Teacher Dashboard
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    # Attendance Management
    path('attendance/', views.attendance_management, name='attendance_management'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/reports/', views.attendance_reports, name='attendance_reports'),
    
    # Grade Management
    path('grades/', views.grade_management, name='grade_management'),
    path('grades/add/', views.add_grade, name='add_grade'),
    path('grades/reports/', views.grade_reports, name='grade_reports'),
    path('grades/edit/<int:grade_id>/', views.edit_grade, name='edit_grade'),
    
    # AJAX endpoints
    path('ajax/students/<int:subject_id>/', views.ajax_get_students, name='ajax_get_students'),
]
