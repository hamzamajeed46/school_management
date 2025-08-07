from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

def is_teacher(user):
    return user.is_authenticated and user.is_teacher()

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    """Teacher dashboard view"""
    context = {
        'user': request.user,
        'page_title': 'Teacher Dashboard',
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)
