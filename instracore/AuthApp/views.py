from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django import forms

from .models import User, Notification, AuditLog, ActivityLog
from .forms import UserRegistrationForm, UserProfileForm


def index(request):
    # Check if there are any users in the system
    if User.objects.count() == 0:
        return redirect('auth:setup')
    
    if request.user.is_authenticated:
        # Redirect to appropriate dashboard based on user role
        if request.user.role == 'admin':
            return redirect('admin_dashboard:dashboard')
        elif request.user.role == 'employee':
            return redirect('employee:dashboard')
        elif request.user.role == 'student':
            return redirect('student:dashboard')
        elif request.user.role == 'candidate':
            return redirect('candidate:dashboard')
    
    # Show public index page
    return render(request, 'AuthApp/index.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('auth:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Log the action
                AuditLog.objects.create(
                    user=user,
                    action=f"User logged in",
                    model_name="User",
                    object_id=str(user.id)
                )
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to appropriate dashboard based on user role
                if user.role == 'admin':
                    return redirect('admin_dashboard:dashboard')
                elif user.role == 'employee':
                    return redirect('employee:dashboard')
                elif user.role == 'student':
                    return redirect('student:dashboard')
                elif user.role == 'candidate':
                    return redirect('candidate:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'AuthApp/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=f"User logged out",
            model_name="User",
            object_id=str(request.user.id)
        )
        
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    
    return redirect('auth:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('auth:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'  # Only students can self-register
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Log the action
            AuditLog.objects.create(
                user=user,
                action=f"New student registered: {user.username}",
                model_name="User",
                object_id=str(user.id)
            )
            
            messages.success(request, f'Account created successfully for {user.username}! You can now log in.')
            return redirect('auth:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'AuthApp/register.html', {'form': form})


def setup_view(request):
    # Only allow setup if there are no users in the system
    if User.objects.count() > 0:
        return redirect('auth:login')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'  # First user must be an admin
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            # Log the action
            AuditLog.objects.create(
                user=user,
                action=f"Initial admin setup: {user.username}",
                model_name="User",
                object_id=str(user.id)
            )
            
            messages.success(request, f'Admin account created successfully for {user.username}! You can now log in.')
            return redirect('auth:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'AuthApp/setup.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Updated profile",
                model_name="User",
                object_id=str(request.user.id)
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('auth:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'form': form,
        'notifications': notifications,
        'active_page': 'profile',
    }
    
    return render(request, 'AuthApp/profile.html', context)


@login_required
def notifications_view(request):
    # Get user notifications
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by read status
    filter_read = request.GET.get('read')
    if filter_read == 'true':
        notifications_list = notifications_list.filter(is_read=True)
    elif filter_read == 'false':
        notifications_list = notifications_list.filter(is_read=False)
    
    # Pagination
    paginator = Paginator(notifications_list, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark all as read if requested
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        notifications_list.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('auth:notifications')
    
    context = {
        'page_obj': page_obj,
        'filter_read': filter_read,
        'active_page': 'notifications',
    }
    
    return render(request, 'AuthApp/notifications.html', context)


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('auth:notifications')


@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully.')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('auth:notifications')
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'AuthApp/notification_confirm_delete.html', context)


@login_required
def dashboard(request):
    user = request.user
    
    # Get user notifications
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get recent activities
    recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:10]
    
    context = {
        'unread_notifications_count': unread_notifications,
        'recent_notifications': recent_notifications,
        'recent_activities': recent_activities,
        'active_page': 'dashboard',
    }
    
    # Render appropriate dashboard template based on user role
    if user.role == 'admin':
        return render(request, 'AuthApp/admin_dashboard.html', context)
    elif user.role == 'employee':
        return render(request, 'AuthApp/employee_dashboard.html', context)
    elif user.role == 'student':
        return render(request, 'AuthApp/student_dashboard.html', context)
    elif user.role == 'candidate':
        return render(request, 'AuthApp/candidate_dashboard.html', context)
    else:
        return render(request, 'AuthApp/dashboard.html', context)