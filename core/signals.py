from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import StudentProfile, TeacherProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create appropriate profile when a user is created"""
    if created:
        if instance.role == 'student':
            # We'll let admin manually create student profiles with required fields
            pass
        elif instance.role == 'teacher':
            # We'll let admin manually create teacher profiles with required fields
            pass

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    # This will be expanded when we have more automatic profile creation logic
    pass
