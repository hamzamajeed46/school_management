from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
]
