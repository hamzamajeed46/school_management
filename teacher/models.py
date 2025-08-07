from django.db import models
from django.conf import settings
from core.models import TeacherProfile

# The main TeacherProfile model is in core.models
# This file can contain teacher-specific models like:

class TeacherSchedule(models.Model):
    """Teacher's weekly schedule"""
    
    WEEKDAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name='schedule'
    )
    weekday = models.CharField(max_length=10, choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey(
        'core.Subject',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    room_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Classroom or room number"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['weekday', 'start_time']
        unique_together = ['teacher', 'weekday', 'start_time']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
