# school_management/views.py
from django.shortcuts import render, redirect

def home(request):
    """Home view with authentication-based redirection"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'home.html')
