from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student Dashboard
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Subject Enrollment
    path('enrollment/', views.subject_enrollment, name='subject_enrollment'),
    path('enroll/<int:subject_id>/', views.enroll_subject, name='enroll_subject'),
    path('unenroll/<int:subject_id>/', views.unenroll_subject, name='unenroll_subject'),
    
    # Grades
    path('grades/', views.view_grades, name='view_grades'),
    path('grades/subject/<int:subject_id>/', views.subject_grades, name='subject_grades'),
    
    # AJAX endpoints
    path('ajax/enroll/<int:subject_id>/', views.ajax_enroll_subject, name='ajax_enroll_subject'),
]
