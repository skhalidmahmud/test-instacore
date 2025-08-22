from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import F
from django.utils.dateparse import parse_date
from datetime import datetime, date
import json
import csv

from AuthApp.models import User, Notification, AuditLog
from EmployeeApp.models import JobPost
from CandidateApp.models import CandidateProfile, JobApplication, InterviewInvitation
from CandidateApp.forms import (
    CandidateProfileForm, JobApplicationForm, InterviewInvitationForm
)


def is_candidate(user):
    return user.role == 'candidate'


@login_required
@user_passes_test(is_candidate)
def dashboard(request):
    candidate = request.user
    
    # Get candidate profile
    try:
        profile = CandidateProfile.objects.get(user=candidate)
    except CandidateProfile.DoesNotExist:
        profile = None
    
    # Get job applications
    applications = JobApplication.objects.filter(candidate=candidate).order_by('-applied_at')
    
    # Get application statistics
    total_applications = applications.count()
    pending_applications = applications.filter(status='applied').count()
    under_review_applications = applications.filter(status='under_review').count()
    interview_scheduled_applications = applications.filter(status='interview_scheduled').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Get upcoming interviews
    upcoming_interviews = InterviewInvitation.objects.filter(
        application__candidate=candidate,
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).order_by('scheduled_date')[:5]
    
    # Get available jobs (excluding jobs already applied to)
    applied_job_ids = applications.values_list('job_post_id', flat=True)
    available_jobs = JobPost.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).exclude(id__in=applied_job_ids).order_by('-created_at')[:10]
    
    context = {
        'profile': profile,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'interview_scheduled_applications': interview_scheduled_applications,
        'rejected_applications': rejected_applications,
        'upcoming_interviews': upcoming_interviews,
        'available_jobs': available_jobs,
        'active_page': 'dashboard',
    }
    return render(request, 'CandidateApp/dashboard.html', context)


@login_required
@user_passes_test(is_candidate)
def profile(request):
    candidate = request.user
    
    # Get or create candidate profile
    try:
        profile = CandidateProfile.objects.get(user=candidate)
    except CandidateProfile.DoesNotExist:
        profile = CandidateProfile.objects.create(user=candidate)
    
    if request.method == 'POST':
        form = CandidateProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action="Updated candidate profile",
                model_name="CandidateProfile",
                object_id=str(profile.id)
            )
            
            messages.success(request, 'Profile updated successfully')
            return redirect('candidate:dashboard')
    else:
        form = CandidateProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'active_page': 'profile',
    }
    return render(request, 'CandidateApp/profile.html', context)


@login_required
@user_passes_test(is_candidate)
def available_jobs(request):
    candidate = request.user
    
    # Get job applications to exclude already applied jobs
    applied_job_ids = JobApplication.objects.filter(
        candidate=candidate
    ).values_list('job_post_id', flat=True)
    
    # Get available jobs
    jobs_list = JobPost.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).exclude(id__in=applied_job_ids).order_by('-created_at')
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        jobs_list = jobs_list.filter(role=role_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        jobs_list = jobs_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(min_requirements__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(jobs_list, 10)  # Show 10 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'active_page': 'available_jobs',
    }
    return render(request, 'CandidateApp/available_jobs.html', context)


@login_required
@user_passes_test(is_candidate)
def job_detail(request, pk):
    candidate = request.user
    job = get_object_or_404(JobPost, pk=pk, is_active=True)
    
    # Check if candidate has already applied
    has_applied = JobApplication.objects.filter(
        candidate=candidate,
        job_post=job
    ).exists()
    
    # Check if job deadline has passed
    is_deadline_passed = job.deadline < timezone.now().date()
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'is_deadline_passed': is_deadline_passed,
        'active_page': 'available_jobs',
    }
    return render(request, 'CandidateApp/job_detail.html', context)


@login_required
@user_passes_test(is_candidate)
def apply_job(request, pk):
    candidate = request.user
    job = get_object_or_404(JobPost, pk=pk, is_active=True)
    
    # Check if candidate has already applied
    if JobApplication.objects.filter(candidate=candidate, job_post=job).exists():
        messages.error(request, 'You have already applied for this job')
        return redirect('candidate:job_detail', pk=job.pk)
    
    # Check if job deadline has passed
    if job.deadline < timezone.now().date():
        messages.error(request, 'The application deadline for this job has passed')
        return redirect('candidate:job_detail', pk=job.pk)
    
    # Check if candidate has a profile
    try:
        profile = CandidateProfile.objects.get(user=candidate)
    except CandidateProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile before applying for jobs')
        return redirect('candidate:profile')
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.candidate = candidate
            application.job_post = job
            application.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Applied for job: {job.title}",
                model_name="JobApplication",
                object_id=str(application.id)
            )
            
            messages.success(request, f'Application for {job.title} submitted successfully')
            return redirect('candidate:my_applications')
    else:
        form = JobApplicationForm()
    
    context = {
        'form': form,
        'job': job,
        'active_page': 'available_jobs',
    }
    return render(request, 'CandidateApp/apply_job.html', context)


@login_required
@user_passes_test(is_candidate)
def my_applications(request):
    candidate = request.user
    
    # Get job applications
    applications_list = JobApplication.objects.filter(candidate=candidate).order_by('-applied_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications_list = applications_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications_list, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'active_page': 'my_applications',
    }
    return render(request, 'CandidateApp/my_applications.html', context)