from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Core/Admin URLs will go here
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
