from django.db import models
from django.utils import timezone
from AuthApp.models import User
from EmployeeApp.models import JobPost


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    expected_salary = models.CharField(max_length=100, blank=True)
    availability = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]
    
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_job_applications')
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='candidate_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('candidate', 'job_post')
    
    def __str__(self):
        return f"{self.candidate.username} - {self.job_post.title}"


class InterviewInvitation(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='candidate_interview_invitations')
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    online_meeting_link = models.URLField(blank=True)
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='candidate_interviews')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')])
    feedback = models.TextField(blank=True)
    
    def __str__(self):
        return f"Interview for {self.application.candidate.username} - {self.application.job_post.title}"