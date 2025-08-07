from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import User
from .forms import CustomUserCreationForm, LoginForm

def user_login(request):
    """Custom login view with role-based redirection"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Role-based redirection
                if user.is_admin():
                    return redirect('core:admin_dashboard')
                elif user.is_teacher():
                    return redirect('teacher:teacher_dashboard')
                elif user.is_student():
                    return redirect('students:student_dashboard')
                else:
                    return redirect('users:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('users:login')

@login_required
def dashboard(request):
    """Main dashboard with role-based content"""
    user = request.user
    context = {
        'user': user,
        'role': user.get_role_display(),
    }
    
    # Role-based template rendering
    if user.is_admin():
        return render(request, 'dashboards/admin_dashboard.html', context)
    elif user.is_teacher():
        return render(request, 'dashboards/teacher_dashboard.html', context)
    elif user.is_student():
        return render(request, 'dashboards/student_dashboard.html', context)
    else:
        return render(request, 'dashboards/default_dashboard.html', context)

class UserRegistrationView(CreateView):
    """User registration view (for admin use)"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        messages.success(self.request, 'User registered successfully!')
        return super().form_valid(form)
