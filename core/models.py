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
    
    def get_attendance_summary(self):
        """Get attendance summary for the student"""
        from django.db.models import Count, Q
        from datetime import date, timedelta
        
        # Get attendance for last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        
        total_classes = self.attendance_records.filter(date__gte=thirty_days_ago).count()
        present_classes = self.attendance_records.filter(
            date__gte=thirty_days_ago,
            status__in=['present', 'late']
        ).count()
        
        attendance_percentage = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0
        
        return {
            'total_classes': total_classes,
            'present_classes': present_classes,
            'absent_classes': total_classes - present_classes,
            'attendance_percentage': attendance_percentage
        }
    
    def get_subject_wise_attendance(self):
        """Get attendance summary by subject"""
        from django.db.models import Count, Q
        
        attendance_data = []
        enrolled_subjects = self.get_enrolled_subjects()
        
        for subject in enrolled_subjects:
            total = self.attendance_records.filter(subject=subject).count()
            present = self.attendance_records.filter(
                subject=subject,
                status__in=['present', 'late']
            ).count()
            
            percentage = round((present / total * 100), 1) if total > 0 else 0
            
            attendance_data.append({
                'subject': subject,
                'total_classes': total,
                'present_classes': present,
                'absent_classes': total - present,
                'attendance_percentage': percentage
            })
        
        return attendance_data
    
    def get_overall_gpa(self):
        """Calculate overall GPA for the student"""
        from django.db.models import Avg
        
        # Get all published grades
        published_grades = self.grades.filter(is_published=True)
        if not published_grades.exists():
            return 0.0
        
        # Calculate average percentage
        avg_percentage = published_grades.aggregate(
            avg=Avg('percentage')
        )['avg']
        
        return round(avg_percentage / 25, 2) if avg_percentage else 0.0  # Convert to 4.0 scale
    
    def get_subject_wise_grades(self):
        """Get grades summary by subject"""
        grades_data = []
        enrolled_subjects = self.get_enrolled_subjects()
        
        for subject in enrolled_subjects:
            subject_grades = self.grades.filter(
                subject=subject,
                is_published=True
            ).order_by('-date_assigned')
            
            if subject_grades.exists():
                avg_percentage = subject_grades.aggregate(
                    avg=models.Avg('percentage')
                )['avg']
                
                grades_data.append({
                    'subject': subject,
                    'grades': subject_grades,
                    'average_percentage': round(avg_percentage, 1) if avg_percentage else 0,
                    'total_assignments': subject_grades.count(),
                    'latest_grade': subject_grades.first() if subject_grades else None
                })
        
        return grades_data
        
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
    
    def get_attendance_overview(self):
        """Get attendance overview for teacher's subjects"""
        from django.db.models import Count, Q
        from datetime import date
        
        today = date.today()
        subjects = self.get_assigned_subjects()
        
        overview = []
        for subject in subjects:
            enrolled_students = subject.get_enrolled_students_count()
            today_attendance = subject.attendance_records.filter(date=today).count()
            present_today = subject.attendance_records.filter(
                date=today,
                status__in=['present', 'late']
            ).count()
            
            overview.append({
                'subject': subject,
                'enrolled_students': enrolled_students,
                'attendance_marked': today_attendance,
                'present_count': present_today,
                'attendance_pending': enrolled_students - today_attendance
            })
        
        return overview
    
    def get_grading_overview(self):
        """Get grading overview for teacher's subjects"""
        subjects = self.get_assigned_subjects()
        grading_data = []
        
        for subject in subjects:
            total_students = subject.get_enrolled_students_count()
            total_grades = subject.grades.count()
            pending_grades = subject.grades.filter(is_published=False).count()
            
            grading_data.append({
                'subject': subject,
                'total_students': total_students,
                'total_grades': total_grades,
                'published_grades': total_grades - pending_grades,
                'pending_grades': pending_grades
            })
        
        return grading_data

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


class Attendance(models.Model):
    """Model to track student attendance for specific subjects"""
    
    ATTENDANCE_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(
        help_text="Date of the class/attendance"
    )
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_CHOICES,
        default='absent',
        help_text="Attendance status for the student"
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about attendance (optional)"
    )
    marked_by = models.ForeignKey(
        'TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance',
        help_text="Teacher who marked this attendance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = ['student', 'subject', 'date']
        ordering = ['-date', 'subject', 'student']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name} ({self.date}) - {self.get_status_display()}"
    
    @property
    def is_present(self):
        """Check if student was present (present or late)"""
        return self.status in ['present', 'late']
    
    @property
    def is_absent(self):
        """Check if student was absent"""
        return self.status in ['absent']


class Grade(models.Model):
    """Model to track student grades for specific subjects"""
    
    GRADE_TYPE_CHOICES = [
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('project', 'Project'),
        ('participation', 'Class Participation'),
        ('homework', 'Homework'),
        ('test', 'Test'),
    ]
    
    LETTER_GRADE_CHOICES = [
        ('A+', 'A+ (97-100)'),
        ('A', 'A (93-96)'),
        ('A-', 'A- (90-92)'),
        ('B+', 'B+ (87-89)'),
        ('B', 'B (83-86)'),
        ('B-', 'B- (80-82)'),
        ('C+', 'C+ (77-79)'),
        ('C', 'C (73-76)'),
        ('C-', 'C- (70-72)'),
        ('D+', 'D+ (67-69)'),
        ('D', 'D (63-66)'),
        ('D-', 'D- (60-62)'),
        ('F', 'F (Below 60)'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    grade_type = models.CharField(
        max_length=20,
        choices=GRADE_TYPE_CHOICES,
        help_text="Type of grade/assessment"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the assignment/test (e.g., 'Math Quiz 1', 'History Essay')"
    )
    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Marks obtained by student"
    )
    total_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Total marks possible"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Percentage score (auto-calculated)"
    )
    letter_grade = models.CharField(
        max_length=2,
        choices=LETTER_GRADE_CHOICES,
        blank=True,
        null=True,
        help_text="Letter grade (auto-calculated)"
    )
    date_assigned = models.DateField(
        help_text="Date when assignment was given"
    )
    date_submitted = models.DateField(
        blank=True,
        null=True,
        help_text="Date when student submitted"
    )
    comments = models.TextField(
        blank=True,
        null=True,
        help_text="Teacher's comments/feedback"
    )
    graded_by = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grades_assigned',
        help_text="Teacher who assigned this grade"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether grade is visible to student"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ['-date_assigned', 'subject', 'student']
        unique_together = ['student', 'subject', 'title', 'grade_type']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.name} - {self.title} ({self.marks_obtained}/{self.total_marks})"
    
    def save(self, *args, **kwargs):
        """Auto-calculate percentage and letter grade"""
        if self.marks_obtained is not None and self.total_marks is not None and self.total_marks > 0:
            self.percentage = round((self.marks_obtained / self.total_marks) * 100, 2)
            self.letter_grade = self.calculate_letter_grade(self.percentage)
        super().save(*args, **kwargs)
    
    def calculate_letter_grade(self, percentage):
        """Calculate letter grade based on percentage"""
        if percentage >= 97:
            return 'A+'
        elif percentage >= 93:
            return 'A'
        elif percentage >= 90:
            return 'A-'
        elif percentage >= 87:
            return 'B+'
        elif percentage >= 83:
            return 'B'
        elif percentage >= 80:
            return 'B-'
        elif percentage >= 77:
            return 'C+'
        elif percentage >= 73:
            return 'C'
        elif percentage >= 70:
            return 'C-'
        elif percentage >= 67:
            return 'D+'
        elif percentage >= 63:
            return 'D'
        elif percentage >= 60:
            return 'D-'
        else:
            return 'F'
    
    @property
    def is_passing(self):
        """Check if grade is passing (60% or above)"""
        return self.percentage >= 60 if self.percentage else False
    
    @property
    def grade_color_class(self):
        """Get CSS class based on grade performance"""
        if not self.percentage:
            return 'text-muted'
        elif self.percentage >= 90:
            return 'text-success'
        elif self.percentage >= 80:
            return 'text-info'
        elif self.percentage >= 70:
            return 'text-warning'
        elif self.percentage >= 60:
            return 'text-primary'
        else:
            return 'text-danger'
