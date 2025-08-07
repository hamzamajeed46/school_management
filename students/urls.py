from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student dashboard
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Subject enrollment
    path('enrollment/', views.subject_enrollment, name='subject_enrollment'),
    path('enroll/<int:subject_id>/', views.enroll_subject, name='enroll_subject'),
    path('unenroll/<int:subject_id>/', views.unenroll_subject, name='unenroll_subject'),
    
    # AJAX endpoints
    path('ajax/enroll/<int:subject_id>/', views.ajax_enroll_subject, name='ajax_enroll_subject'),
]
