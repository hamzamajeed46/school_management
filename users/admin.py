from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin with role management"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Additional Info', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'address')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Additional Info', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'address')
        }),
    )
