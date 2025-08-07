from django.contrib import admin
from .models import StudentNote

@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    """Admin interface for StudentNote model"""
    
    list_display = ['get_student_name', 'title', 'created_by', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at', 'student__class_assigned']
    search_fields = [
        'student__user__first_name', 'student__user__last_name',
        'student__student_id', 'title', 'content'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['student', 'created_by']
    
    fieldsets = (
        ('Note Information', {
            'fields': ('student', 'title', 'content')
        }),
        ('Settings', {
            'fields': ('created_by', 'is_private')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username
    get_student_name.short_description = 'Student'
