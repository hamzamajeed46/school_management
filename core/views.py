from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_admin()

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard view"""
    context = {
        'user': request.user,
        'page_title': 'Admin Dashboard',
    }
    return render(request, 'dashboards/admin_dashboard.html', context)
