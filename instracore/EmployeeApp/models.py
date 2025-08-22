from django.db import models
from AuthApp.models import User


# HR Models
class JobPost(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('faculty', 'Faculty'),
        ('hr', 'HR'),
        ('finance', 'Finance'),
        ('marketing', 'Marketing'),
        ('it', 'IT'),
        ('teacher', 'Teacher'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    min_requirements = models.TextField()
    salary_range = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    language = models.CharField(max_length=50, default='English')
    availability = models.CharField(max_length=100)
    application_instructions = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]
    
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True)


class InterviewSchedule(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interviews")
    scheduled_date = models.DateTimeField()
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="interviews_conducted")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')])
    feedback = models.TextField(blank=True)


# Finance Models
class Salary(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="salaries")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="salaries_approved")
    payment_date = models.DateField(blank=True, null=True)
    
    class Meta:
        unique_together = ('employee', 'month')


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies'),
        ('marketing', 'Marketing'),
        ('travel', 'Travel'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="expenses_created")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="expenses_approved")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')])


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('fee', 'Fee Payment'),
        ('salary', 'Salary Payment'),
        ('expense', 'Expense'),
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


# Faculty/Teacher Models
class Course(models.Model):
    TYPE_CHOICES = [
        ('online', 'Online'),
        ('regular', 'Regular'),
        ('diploma', 'Diploma'),
        ('offline', 'Offline'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    course_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration = models.CharField(max_length=50)  # e.g., "8 weeks", "3 months"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="courses_created")
    created_at = models.DateTimeField(auto_now_add=True)
    syllabus = models.FileField(upload_to='syllabi/', blank=True, null=True)
    
    def __str__(self):
        return self.title


class CourseTeacher(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="teachers")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses_teaching")
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="teacher_assignments")
    
    class Meta:
        unique_together = ('course', 'teacher')


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="assignments_created")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


class LessonPlan(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lesson_plans")
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="lesson_plans_created")
    created_at = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'On Leave'),
        ('late', 'Late'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="present")
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="attendance_marked")
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('user', 'date')


class ClassRoutine(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_routines')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='class_routines')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('teacher', 'course', 'day_of_week', 'start_time')