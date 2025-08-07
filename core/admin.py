from django.contrib import admin
from .models import Class, Subject, StudentProfile, TeacherProfile, StudentSubjectEnrollment

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """Admin interface for Class model"""
    
    list_display = ['name', 'academic_year', 'capacity', 'get_student_count', 'get_subject_count', 'is_active', 'created_at']
    list_filter = ['academic_year', 'is_active', 'created_at']
    search_fields = ['name', 'academic_year', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'academic_year')
        }),
        ('Configuration', {
            'fields': ('capacity', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_count(self, obj):
        return obj.get_student_count()
    get_student_count.short_description = 'Students'
    
    def get_subject_count(self, obj):
        return obj.get_subject_count()
    get_subject_count.short_description = 'Subjects'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for Subject model"""
    
    list_display = ['name', 'code', 'class_assigned', 'teacher', 'credits', 'is_mandatory', 'is_active', 'get_enrolled_students_count']
    list_filter = ['class_assigned', 'is_mandatory', 'is_active', 'credits', 'created_at']
    search_fields = ['name', 'code', 'description', 'teacher__user__first_name', 'teacher__user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['teacher']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Assignment', {
            'fields': ('class_assigned', 'teacher')
        }),
        ('Configuration', {
            'fields': ('credits', 'is_mandatory', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_enrolled_students_count(self, obj):
        return obj.get_enrolled_students_count()
    get_enrolled_students_count.short_description = 'Enrolled Students'

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile model"""
    
    list_display = ['get_student_name', 'student_id', 'class_assigned', 'admission_date', 'guardian_name', 'is_active']
    list_filter = ['class_assigned', 'admission_date', 'is_active', 'created_at']
    search_fields = [
        'student_id', 'user__username', 'user__first_name', 'user__last_name',
        'guardian_name', 'guardian_phone', 'guardian_email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user', 'class_assigned']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'student_id', 'class_assigned', 'admission_date')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_phone', 'guardian_email', 'emergency_contact')
        }),
        ('Additional Information', {
            'fields': ('medical_info', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_student_name.short_description = 'Student Name'

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """Admin interface for TeacherProfile model"""
    
    list_display = ['get_teacher_name', 'employee_id', 'qualification', 'specialization', 'experience_years', 'get_subjects_count', 'is_active']
    list_filter = ['qualification', 'joining_date', 'is_active', 'experience_years', 'created_at']
    search_fields = [
        'employee_id', 'user__username', 'user__first_name', 'user__last_name',
        'specialization', 'qualification'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('user', 'employee_id', 'joining_date')
        }),
        ('Qualifications', {
            'fields': ('qualification', 'specialization', 'experience_years')
        }),
        ('Employment Details', {
            'fields': ('salary', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_teacher_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_teacher_name.short_description = 'Teacher Name'



@admin.register(StudentSubjectEnrollment)
class StudentSubjectEnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for StudentSubjectEnrollment model"""
    
    list_display = ['get_student_name', 'get_subject_name', 'get_class_name', 'enrollment_date', 'is_active']
    list_filter = ['subject__class_assigned', 'enrollment_date', 'is_active', 'created_at']
    search_fields = [
        'student__user__first_name', 'student__user__last_name', 'student__student_id',
        'subject__name', 'subject__code'
    ]
    readonly_fields = ['enrollment_date', 'created_at', 'updated_at']
    autocomplete_fields = ['student', 'subject']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'subject', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('enrollment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username
    get_student_name.short_description = 'Student'
    
    def get_subject_name(self, obj):
        return obj.subject.name
    get_subject_name.short_description = 'Subject'
    
    def get_class_name(self, obj):
        return obj.subject.class_assigned.name
    get_class_name.short_description = 'Class'
