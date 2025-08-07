from django.db import models
from django.conf import settings
from core.models import StudentProfile

# The main StudentProfile model is in core.models
# This file can contain student-specific models like:

class StudentNote(models.Model):
    """Notes or remarks about students"""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User who created this note"
    )
    is_private = models.BooleanField(
        default=False,
        help_text="Whether this note is private to staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.student.user.get_full_name()}: {self.title}"
