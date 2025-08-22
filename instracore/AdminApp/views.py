from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.dateparse import parse_date
from calendar import monthcalendar
from datetime import datetime, date
import json
import csv

from AuthApp.models import User, Notification, AuditLog
from AuthApp.forms import UserCreationForm
from AdminApp.forms import UserUpdateForm
from AdminApp.models import Event, Notice, WeekendCalendar, FinancialOverview
from AdminApp.forms import EventForm, NoticeForm, WeekendCalendarForm, FinancialOverviewForm
from EmployeeApp.models import Course, CourseTeacher, Attendance, Salary, Expense, Transaction
from StudentApp.models import Enrollment, ExamResult, Certificate, FeePayment


def is_admin(user):
    return user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Summary statistics
    total_students = User.objects.filter(role='student').count()
    active_students = User.objects.filter(role='student', is_active=True).count()
    inactive_students = total_students - active_students
    
    total_teachers = User.objects.filter(role='employee', sub_role='teacher').count()
    active_teachers = User.objects.filter(role='employee', sub_role='teacher', is_active=True).count()
    inactive_teachers = total_teachers - active_teachers
    
    total_staff = User.objects.filter(role='employee').exclude(sub_role='teacher').count()
    active_staff = User.objects.filter(role='employee', is_active=True).exclude(sub_role='teacher').count()
    inactive_staff = total_staff - active_staff
    
    total_courses = Course.objects.count()
    active_courses = Course.objects.filter(status='active').count()
    inactive_courses = total_courses - active_courses
    
    # Financial overview
    current_month = timezone.now().date().replace(day=1)
    try:
        financial_overview = FinancialOverview.objects.get(month=current_month)
        income = financial_overview.income
        expenses = financial_overview.expenses
        fees_collected = financial_overview.fees_collected
        salaries_paid = financial_overview.salaries_paid
    except FinancialOverview.DoesNotExist:
        income = expenses = fees_collected = salaries_paid = 0
    
    # Recent activities
    recent_activities = AuditLog.objects.all().order_by('-created_at')[:10]
    
    # Upcoming events
    upcoming_events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:5]
    
    # Recent notices
    recent_notices = Notice.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Attendance overview
    today = timezone.now().date()
    student_attendance = Attendance.objects.filter(user__role='student', date=today).count()
    teacher_attendance = Attendance.objects.filter(user__role='employee', user__sub_role='teacher', date=today).count()
    staff_attendance = Attendance.objects.filter(user__role='employee', date=today).exclude(user__sub_role='teacher').count()
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'inactive_teachers': inactive_teachers,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': inactive_staff,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'inactive_courses': inactive_courses,
        'income': income,
        'expenses': expenses,
        'fees_collected': fees_collected,
        'salaries_paid': salaries_paid,
        'recent_activities': recent_activities,
        'upcoming_events': upcoming_events,
        'recent_notices': recent_notices,
        'student_attendance': student_attendance,
        'teacher_attendance': teacher_attendance,
        'staff_attendance': staff_attendance,
        'active_page': 'dashboard',
    }
    return render(request, 'AdminApp/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_management(request):
    users = User.objects.all().order_by('username')
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'active_page': 'user_management',
    }
    return render(request, 'AdminApp/users.html', context)


@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set default password based on role
            default_password = form.cleaned_data['role']
            if form.cleaned_data['sub_role']:
                default_password = form.cleaned_data['sub_role']
            user.set_password(default_password)
            user.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created new user: {user.username}",
                model_name="User",
                object_id=str(user.id)
            )
            
            messages.success(request, f'User {user.username} created successfully. Default password: {default_password}')
            return redirect('admin:user_management')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'title': 'Create User',
        'active_page': 'user_management',
    }
    return render(request, 'AdminApp/user_form.html', context)


@login_required
@user_passes_test(is_admin)
def update_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Updated user: {user.username}",
                model_name="User",
                object_id=str(user.id)
            )
            
            messages.success(request, f'User {user.username} updated successfully')
            return redirect('admin:user_management')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
        'title': 'Update User',
        'active_page': 'user_management',
    }
    return render(request, 'AdminApp/user_form.html', context)


@login_required
@user_passes_test(is_admin)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        # Log the action before deletion
        AuditLog.objects.create(
            user=request.user,
            action=f"Deleted user: {user.username}",
            model_name="User",
            object_id=str(user.id)
        )
        
        user.delete()
        messages.success(request, f'User {user.username} deleted successfully')
        return redirect('admin:user_management')
    
    context = {
        'user_obj': user,
        'active_page': 'user_management',
    }
    return render(request, 'AdminApp/user_confirm_delete.html', context)


@login_required
@user_passes_test(is_admin)
def courses(request):
    courses_list = Course.objects.all().order_by('title')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        courses_list = courses_list.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        courses_list = courses_list.filter(course_type=type_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        courses_list = courses_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(courses_list, 10)  # Show 10 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search_query': search_query,
        'active_page': 'courses',
    }
    return render(request, 'AdminApp/courses.html', context)


@login_required
@user_passes_test(is_admin)
def attendance(request):
    attendance_list = Attendance.objects.all().order_by('-date')
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            parsed_date = parse_date(date_filter)
            if parsed_date:
                attendance_list = attendance_list.filter(date=parsed_date)
        except ValueError:
            pass
    
    # Filter by attendee type
    attendee_type_filter = request.GET.get('attendee_type')
    if attendee_type_filter:
        if attendee_type_filter == 'student':
            attendance_list = attendance_list.filter(user__role='student')
        elif attendee_type_filter == 'teacher':
            attendance_list = attendance_list.filter(user__role='employee', user__sub_role='teacher')
        elif attendee_type_filter == 'staff':
            attendance_list = attendance_list.filter(user__role='employee').exclude(user__sub_role='teacher')
    
    # Pagination
    paginator = Paginator(attendance_list, 20)  # Show 20 attendance records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'date_filter': date_filter,
        'attendee_type_filter': attendee_type_filter,
        'active_page': 'attendance',
    }
    return render(request, 'AdminApp/attendance.html', context)


@login_required
@user_passes_test(is_admin)
def events_notices(request):
    events = Event.objects.all().order_by('-date')
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'events': events,
        'notices': notices,
        'active_page': 'events_notices',
    }
    return render(request, 'AdminApp/events_notices.html', context)


@login_required
@user_passes_test(is_admin)
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created event: {event.title}",
                model_name="Event",
                object_id=str(event.id)
            )
            
            messages.success(request, f'Event {event.title} created successfully')
            return redirect('admin:events_notices')
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'title': 'Create Event',
        'active_page': 'events_notices',
    }
    return render(request, 'AdminApp/event_form.html', context)


@login_required
@user_passes_test(is_admin)
def create_notice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created notice: {notice.title}",
                model_name="Notice",
                object_id=str(notice.id)
            )
            
            messages.success(request, f'Notice {notice.title} created successfully')
            return redirect('admin:events_notices')
    else:
        form = NoticeForm()
    
    context = {
        'form': form,
        'title': 'Create Notice',
        'active_page': 'events_notices',
    }
    return render(request, 'AdminApp/notice_form.html', context)


@login_required
@user_passes_test(is_admin)
def accounts(request):
    # Get current month
    current_month = timezone.now().date().replace(day=1)
    
    try:
        financial_overview = FinancialOverview.objects.get(month=current_month)
    except FinancialOverview.DoesNotExist:
        financial_overview = None
    
    # Get recent transactions
    recent_transactions = Transaction.objects.all().order_by('-date')[:10]
    
    # Get recent expenses
    recent_expenses = Expense.objects.all().order_by('-date')[:10]
    
    # Get recent salaries
    recent_salaries = Salary.objects.all().order_by('-created_at')[:10]
    
    # Get unpaid fees
    unpaid_fees = FeePayment.objects.filter(status='pending').order_by('due_date')[:10]
    
    context = {
        'financial_overview': financial_overview,
        'recent_transactions': recent_transactions,
        'recent_expenses': recent_expenses,
        'recent_salaries': recent_salaries,
        'unpaid_fees': unpaid_fees,
        'active_page': 'accounts',
    }
    return render(request, 'AdminApp/accounts.html', context)


@login_required
@user_passes_test(is_admin)
def reports(request):
    # Get filter parameters
    report_type = request.GET.get('type', 'user')
    period = request.GET.get('period', 'monthly')
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)
    
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month
    
    context = {
        'report_type': report_type,
        'period': period,
        'year': year,
        'month': month,
        'active_page': 'reports',
    }
    
    if report_type == 'user':
        return user_report(request, context)
    elif report_type == 'course':
        return course_report(request, context)
    elif report_type == 'attendance':
        return attendance_report(request, context)
    elif report_type == 'financial':
        return financial_report(request, context)
    else:
        return render(request, 'AdminApp/reports.html', context)


def user_report(request, context):
    # Get filter parameters
    period = context['period']
    year = context['year']
    month = context['month']
    
    # Get users based on filters
    users = User.objects.all()
    
    if period == 'yearly':
        # Filter users created in the specified year
        users = users.filter(date_joined__year=year)
    elif period == 'monthly':
        # Filter users created in the specified month and year
        users = users.filter(date_joined__year=year, date_joined__month=month)
    
    # Group by role
    user_stats = {
        'total': users.count(),
        'admin': users.filter(role='admin').count(),
        'student': users.filter(role='student').count(),
        'employee': users.filter(role='employee').count(),
        'candidate': users.filter(role='candidate').count(),
    }
    
    # Group by subrole for employees
    employee_subroles = {}
    for subrole in ['faculty', 'hr', 'finance', 'marketing', 'it', 'teacher', 'other']:
        employee_subroles[subrole] = users.filter(role='employee', sub_role=subrole).count()
    
    context.update({
        'user_stats': user_stats,
        'employee_subroles': employee_subroles,
        'users': users,
    })
    
    return render(request, 'AdminApp/user_report.html', context)


def course_report(request, context):
    # Get filter parameters
    period = context['period']
    year = context['year']
    month = context['month']
    
    # Get courses based on filters
    courses = Course.objects.all()
    
    if period == 'yearly':
        # Filter courses created in the specified year
        courses = courses.filter(created_at__year=year)
    elif period == 'monthly':
        # Filter courses created in the specified month and year
        courses = courses.filter(created_at__year=year, created_at__month=month)
    
    # Group by status
    course_stats = {
        'total': courses.count(),
        'draft': courses.filter(status='draft').count(),
        'pending_approval': courses.filter(status='pending_approval').count(),
        'active': courses.filter(status='active').count(),
        'inactive': courses.filter(status='inactive').count(),
        'closed': courses.filter(status='closed').count(),
    }
    
    # Group by type
    course_types = {}
    for course_type in ['online', 'regular', 'diploma', 'offline']:
        course_types[course_type] = courses.filter(course_type=course_type).count()
    
    context.update({
        'course_stats': course_stats,
        'course_types': course_types,
        'courses': courses,
    })
    
    return render(request, 'AdminApp/course_report.html', context)


def attendance_report(request, context):
    # Get filter parameters
    period = context['period']
    year = context['year']
    month = context['month']
    
    # Get attendance records based on filters
    attendance_records = Attendance.objects.all()
    
    if period == 'yearly':
        # Filter attendance records in the specified year
        attendance_records = attendance_records.filter(date__year=year)
    elif period == 'monthly':
        # Filter attendance records in the specified month and year
        attendance_records = attendance_records.filter(date__year=year, date__month=month)
    
    # Group by status
    attendance_stats = {
        'total': attendance_records.count(),
        'present': attendance_records.filter(status='present').count(),
        'absent': attendance_records.filter(status='absent').count(),
        'leave': attendance_records.filter(status='leave').count(),
        'late': attendance_records.filter(status='late').count(),
    }
    
    # Group by user type
    user_types = {
        'student': attendance_records.filter(user__role='student').count(),
        'teacher': attendance_records.filter(user__role='employee', user__sub_role='teacher').count(),
        'staff': attendance_records.filter(user__role='employee').exclude(user__sub_role='teacher').count(),
    }
    
    context.update({
        'attendance_stats': attendance_stats,
        'user_types': user_types,
        'attendance_records': attendance_records,
    })
    
    return render(request, 'AdminApp/attendance_report.html', context)


def financial_report(request, context):
    # Get filter parameters
    period = context['period']
    year = context['year']
    month = context['month']
    
    # Get financial records based on filters
    financial_overviews = FinancialOverview.objects.all()
    
    if period == 'yearly':
        # Filter financial overviews in the specified year
        financial_overviews = financial_overviews.filter(month__year=year)
    elif period == 'monthly':
        # Filter financial overviews in the specified month and year
        financial_overviews = financial_overviews.filter(month__year=year, month__month=month)
    
    # Calculate totals
    total_income = sum(overview.income for overview in financial_overviews)
    total_expenses = sum(overview.expenses for overview in financial_overviews)
    total_fees_collected = sum(overview.fees_collected for overview in financial_overviews)
    total_salaries_paid = sum(overview.salaries_paid for overview in financial_overviews)
    
    # Get transactions
    transactions = Transaction.objects.all()
    
    if period == 'yearly':
        # Filter transactions in the specified year
        transactions = transactions.filter(date__year=year)
    elif period == 'monthly':
        # Filter transactions in the specified month and year
        transactions = transactions.filter(date__year=year, date__month=month)
    
    # Group transactions by type
    transaction_types = {}
    for transaction_type in ['fee', 'salary', 'expense', 'purchase', 'refund', 'other']:
        transaction_types[transaction_type] = transactions.filter(transaction_type=transaction_type).count()
    
    context.update({
        'financial_overviews': financial_overviews,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_fees_collected': total_fees_collected,
        'total_salaries_paid': total_salaries_paid,
        'transactions': transactions,
        'transaction_types': transaction_types,
    })
    
    return render(request, 'AdminApp/financial_report.html', context)