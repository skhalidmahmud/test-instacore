from django import forms
from django.utils import timezone
from AuthApp.models import User
from EmployeeApp.models import JobPost
from CandidateApp.models import (
    CandidateProfile, JobApplication, InterviewInvitation
)


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ('resume', 'skills', 'experience', 'education', 'expected_salary', 'availability')


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'notes')


class InterviewInvitationForm(forms.ModelForm):
    class Meta:
        model = InterviewInvitation
        fields = ('scheduled_date', 'location', 'online_meeting_link', 'notes')
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }