from django.contrib import admin
from .models import TeacherSchedule

@admin.register(TeacherSchedule)
class TeacherScheduleAdmin(admin.ModelAdmin):
    """Admin interface for TeacherSchedule model"""
    
    list_display = ['get_teacher_name', 'weekday', 'start_time', 'end_time', 'subject', 'room_number', 'is_active']
    list_filter = ['weekday', 'is_active', 'teacher__user__last_name', 'created_at']
    search_fields = [
        'teacher__user__first_name', 'teacher__user__last_name',
        'teacher__employee_id', 'subject__name', 'room_number'
    ]
    readonly_fields = ['created_at']
    autocomplete_fields = ['teacher', 'subject']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('teacher', 'weekday', 'start_time', 'end_time')
        }),
        ('Class Details', {
            'fields': ('subject', 'room_number')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_teacher_name(self, obj):
        return obj.teacher.user.get_full_name() or obj.teacher.user.username
    get_teacher_name.short_description = 'Teacher'
