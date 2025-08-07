from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    # Teacher-specific URLs will go here
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
]
