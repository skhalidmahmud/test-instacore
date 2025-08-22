from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import User, ActivityLog
from .forms import UserRegistrationForm, UserProfileForm
from django.db.models import Q

def index(request):
    # If no user exists, redirect to setup
    if not User.objects.exists():
        return redirect('setup')
    
    # If user is authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'index.html')

def setup(request):
    # If users already exist, redirect to login
    if User.objects.filter(role='admin').exists():
        return redirect('auth:login')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user without saving to database yet
            user = form.save(commit=False)
            user.role = 'admin'  # Set role to admin
            user.is_staff = True  # Allow access to admin panel
            user.is_superuser = False  # NOT a superuser
            user.is_active = True  # Account is active immediately
            # Set password properly
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action="Admin account created during setup"
            )
            
            messages.success(request, 'Admin account created successfully! Please login.')
            return redirect('auth:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'AuthApp/setup.html', {'form': form})

def register(request):
    if not User.objects.filter(role='admin').exists():
        return redirect('auth:setup')
    # Only students can register
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True  # Account is active immediately
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action="Student account created"
            )
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('auth:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'AuthApp/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                # Log activity
                ActivityLog.objects.create(user=user, action="Logged in")
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'employee':
                    if user.sub_role == 'hr':
                        return redirect('hr_dashboard')
                    elif user.sub_role == 'faculty':
                        return redirect('faculty_dashboard')
                    elif user.sub_role == 'finance':
                        return redirect('finance_dashboard')
                    elif user.sub_role == 'teacher':
                        return redirect('teacher_dashboard')
                    else:
                        return redirect('other_dashboard')
                elif user.role == 'student':
                    return redirect('student_dashboard')
                elif user.role == 'candidate':
                    return redirect('candidate_dashboard')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, 'Your account is not active. Please contact support.')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'AuthApp/login.html')

@login_required
def logout_view(request):
    # Log activity
    ActivityLog.objects.create(user=request.user, action="Logged out")
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

@login_required
def dashboard(request):
    user = request.user
    role = user.role
    
    # Redirect based on role
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'employee':
        sub_role = user.sub_role
        if sub_role == 'hr':
            return redirect('hr_dashboard')
        elif sub_role == 'faculty':
            return redirect('faculty_dashboard')
        elif sub_role == 'finance':
            return redirect('finance_dashboard')
        elif sub_role == 'teacher':
            return redirect('teacher_dashboard')
        else:
            return redirect('other_dashboard')
    elif role == 'student':
        return redirect('student_dashboard')
    elif role == 'candidate':
        return redirect('candidate_dashboard')
    else:
        return redirect('index')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            ActivityLog.objects.create(user=request.user, action="Profile updated")
            messages.success(request, 'Profile updated successfully!')
            return redirect('auth:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'AuthApp/profile.html', {'form': form})

@login_required
def notifications(request):
    # Mark all notifications as read when viewing
    request.user.notifications.filter(is_read=False).update(is_read=True)
    notifications = request.user.notifications.all().order_by('-created_at')
    return render(request, 'AuthApp/notifications.html', {'notifications': notifications})

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent the user from being logged out
            login(request, user)
            ActivityLog.objects.create(user=request.user, action="Password changed")
            messages.success(request, 'Your password was successfully updated!')
            return redirect('auth:password_change_done')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'AuthApp/password_change.html', {'form': form})

@login_required
def password_change_done(request):
    return render(request, 'AuthApp/password_change_done.html')

class CustomPasswordResetView(PasswordResetView):
    template_name = 'AuthApp/password_reset.html'
    email_template_name = 'AuthApp/password_reset_email.html'
    subject_template_name = 'AuthApp/password_reset_subject.txt'
    success_url = '/auth/password-reset/done/'
    from_email = settings.DEFAULT_FROM_EMAIL
    
    def form_valid(self, form):
        # Log password reset request
        try:
            user = User.objects.get(email=form.cleaned_data['email'])
            ActivityLog.objects.create(user=user, action="Password reset requested")
        except User.DoesNotExist:
            pass
        return super().form_valid(form)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'AuthApp/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'AuthApp/password_reset_confirm.html'
    success_url = '/auth/reset/done/'
    
    def form_valid(self, form):
        # Log password reset completion
        user = form.save()
        ActivityLog.objects.create(user=user, action="Password reset completed")
        return super().form_valid(form)

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'AuthApp/password_reset_complete.html'

@login_required
def delete_account(request):
    if request.method == 'POST':
        # Log account deletion
        ActivityLog.objects.create(user=request.user, action="Account deletion requested")
        
        # Create a backup of user data in Trash model
        from .models import Trash
        import json
        
        user_data = {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'role': request.user.role,
            'sub_role': request.user.sub_role,
            'date_joined': request.user.date_joined.isoformat(),
        }
        
        Trash.objects.create(
            model_name='User',
            object_data=user_data,
            deleted_by=request.user
        )
        
        # Logout and delete user
        logout(request)
        request.user.delete()
        
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('auth:account_deleted')
    
    return render(request, 'AuthApp/delete_account.html')

def account_deleted(request):
    return render(request, 'AuthApp/account_deleted.html')

def verify_email(request, token):
    try:
        uid = force_str(urlsafe_base64_decode(token.split('-')[0]))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            ActivityLog.objects.create(user=user, action="Email verified")
            messages.success(request, 'Your email has been verified. You can now login.')
            return redirect('auth:login')
        else:
            messages.error(request, 'The verification link is invalid or has expired.')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'The verification link is invalid or has expired.')
    
    return redirect('auth:login')

@login_required
def resend_verification(request):
    if request.user.is_active:
        messages.info(request, 'Your account is already verified.')
        return redirect('dashboard')
    
    # Generate verification token
    token = default_token_generator.make_token(request.user)
    uid = urlsafe_base64_encode(force_bytes(request.user.pk))
    verification_link = request.build_absolute_uri(f'/auth/verify-email/{uid}-{token}/')
    
    # Send verification email
    subject = 'Verify your email address'
    message = f'Hi {request.user.username},\n\nPlease click the following link to verify your email address:\n\n{verification_link}\n\nIf you did not request this, please ignore this email.\n\nThanks,\nThe InstaCore Team'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        fail_silently=False,
    )
    
    ActivityLog.objects.create(user=request.user, action="Verification email resent")
    messages.success(request, 'A verification email has been sent to your email address.')
    return redirect('dashboard')

# Password reset views
password_reset = CustomPasswordResetView.as_view()
password_reset_done = CustomPasswordResetDoneView.as_view()
password_reset_confirm = CustomPasswordResetConfirmView.as_view()
password_reset_complete = CustomPasswordResetCompleteView.as_view()