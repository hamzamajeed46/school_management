from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Class(models.Model):
    """Model representing a class/grade in the school"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g., '10-A', 'Grade 9', 'Class 12-Science'"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional information about the class"
    )
    academic_year = models.CharField(
        max_length=20,
        help_text="e.g., '2024-2025'"
    )
    capacity = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum number of students in this class"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this class is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.academic_year})"
    
    def get_student_count(self):
        """Get the number of students in this class"""
        return self.students.count()
    
    def get_subject_count(self):
        """Get the number of subjects for this class"""
        return self.subjects.count()

class Subject(models.Model):
    """Model representing a subject taught in the school"""
    
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Mathematics', 'English Literature', 'Physics'"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique subject code, e.g., 'MATH101', 'ENG201'"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Subject description and objectives"
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='subjects',
        help_text="The class this subject is taught to"
    )
    teacher = models.ForeignKey(
        'TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects_taught',
        help_text="Teacher assigned to this subject"
    )
    credits = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Credit hours for this subject"
    )
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Whether this subject is mandatory or optional"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this subject is currently being taught"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ['class_assigned', 'name']
        unique_together = ['name', 'class_assigned']
    
    def __str__(self):
        return f"{self.name} ({self.class_assigned.name})"
    
    def get_enrolled_students_count(self):
        """Get the number of students enrolled in this subject"""
        return self.enrolled_students.count()

class StudentProfile(models.Model):
    """Extended profile for student users"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique student identification number"
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text="Class the student belongs to"
    )
    admission_date = models.DateField(
        help_text="Date when student was admitted"
    )
    guardian_name = models.CharField(
        max_length=100,
        help_text="Name of parent/guardian"
    )
    guardian_phone = models.CharField(
        max_length=15,
        help_text="Guardian's contact number"
    )
    guardian_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Guardian's email address"
    )
    emergency_contact = models.CharField(
        max_length=15,
        help_text="Emergency contact number"
    )
    medical_info = models.TextField(
        blank=True,
        null=True,
        help_text="Any medical conditions or allergies"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the student is currently enrolled"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        ordering = ['student_id']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_id})"
    
    def get_enrolled_subjects(self):
        """Get all subjects the student is enrolled in"""
        return Subject.objects.filter(enrolled_students__student=self)
    
    def get_enrollment_count(self):
        """Get the number of subjects student is enrolled in"""
        return self.enrollments.count()
    
    def get_available_subjects(self):
        """Get subjects available for enrollment (not already enrolled)"""
        if not self.class_assigned:
            return Subject.objects.none()
        
        enrolled_subject_ids = self.enrollments.filter(is_active=True).values_list('subject_id', flat=True)
        return self.class_assigned.subjects.filter(
            is_active=True
        ).exclude(id__in=enrolled_subject_ids)
    
    def can_enroll_in_subject(self, subject):
        """Check if student can enroll in a specific subject"""
        # Check if subject is for student's class
        if not self.class_assigned or subject.class_assigned != self.class_assigned:
            return False, "Subject is not available for your class"
        
        # Check if already enrolled
        if self.enrollments.filter(subject=subject, is_active=True).exists():
            return False, "Already enrolled in this subject"
        
        # Check maximum subjects limit (e.g., 8 subjects max)
        if self.get_enrollment_count() >= 8:
            return False, "Maximum subject limit reached (8 subjects)"
        
        # Check if subject is active
        if not subject.is_active:
            return False, "Subject is not currently active"
        
        return True, "Can enroll"
    
    def enroll_in_subject(self, subject):
        """Enroll student in a subject"""
        can_enroll, message = self.can_enroll_in_subject(subject)
        if not can_enroll:
            return False, message
        
        enrollment, created = StudentSubjectEnrollment.objects.get_or_create(
            student=self,
            subject=subject,
            defaults={'is_active': True}
        )
        
        if not created and not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save()
            return True, "Successfully re-enrolled in subject"
        elif created:
            return True, "Successfully enrolled in subject"
        else:
            return False, "Already enrolled in this subject"
    
    
    def unenroll_from_subject(self, subject):
        """Unenroll student from a subject"""
        try:
            # Find the enrollment record
            enrollment = StudentSubjectEnrollment.objects.filter(
                student=self, 
                subject=subject, 
                is_active=True
            ).first()
            
            if not enrollment:
                return False, "You are not enrolled in this subject"
            
            # Check if subject is mandatory
            if subject.is_mandatory:
                return False, "Cannot unenroll from mandatory subjects"
            
            # Delete the enrollment record (or set is_active=False if you want to keep history)
            enrollment.delete()
            # Alternative: enrollment.is_active = False; enrollment.save()
            
            return True, f"Successfully unenrolled from {subject.name}"
            
        except Exception as e:
            return False, f"Error during unenrollment: {str(e)}"
        
class TeacherProfile(models.Model):
    """Extended profile for teacher users"""
    
    QUALIFICATION_CHOICES = [
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
        ('diploma', 'Diploma'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique teacher/employee identification number"
    )
    qualification = models.CharField(
        max_length=20,
        choices=QUALIFICATION_CHOICES,
        help_text="Highest educational qualification"
    )
    specialization = models.CharField(
        max_length=100,
        help_text="Subject specialization or field of expertise"
    )
    experience_years = models.PositiveIntegerField(
        default=0,
        help_text="Years of teaching experience"
    )
    joining_date = models.DateField(
        help_text="Date when teacher joined the institution"
    )
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly salary (optional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the teacher is currently employed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Teacher Profile"
        verbose_name_plural = "Teacher Profiles"
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"
    
    def get_assigned_subjects(self):
        """Get all subjects assigned to this teacher"""
        return self.subjects_taught.filter(is_active=True)
    
    def get_subjects_count(self):
        """Get the number of subjects assigned to teacher"""
        return self.subjects_taught.filter(is_active=True).count()
    
    def get_total_students(self):
        """Get total number of students across all subjects"""
        subjects = self.get_assigned_subjects()
        total = 0
        for subject in subjects:
            total += subject.get_enrolled_students_count()
        return total

class StudentSubjectEnrollment(models.Model):
    """Model to handle student enrollment in subjects"""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrolled_students'
    )
    enrollment_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the student enrolled in this subject"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the enrollment is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Student Subject Enrollment"
        verbose_name_plural = "Student Subject Enrollments"
        unique_together = ['student', 'subject']
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} enrolled in {self.subject.name}"
    
    def can_unenroll(self):
        """Check if student can unenroll from this subject"""
        return not self.subject.is_mandatory
