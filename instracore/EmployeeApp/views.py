from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import F
from django.utils.dateparse import parse_date
from datetime import datetime, date, timedelta
import json
import csv

from AuthApp.models import User, Notification, AuditLog
from EmployeeApp.models import (
    JobPost, Application, InterviewSchedule, Salary, Expense, Transaction,
    Course, CourseTeacher, Assignment, LessonPlan, Attendance, ClassRoutine
)
from EmployeeApp.forms import (
    JobPostForm, ApplicationForm, InterviewScheduleForm, SalaryForm, ExpenseForm, TransactionForm,
    CourseForm, CourseTeacherForm, AssignmentForm, LessonPlanForm, AttendanceForm, ClassRoutineForm
)
from StudentApp.models import Enrollment


# Role check functions
def is_employee(user):
    return user.role == 'employee'

def is_hr(user):
    return user.role == 'employee' and user.sub_role == 'hr'

def is_finance(user):
    return user.role == 'employee' and user.sub_role == 'finance'

def is_faculty(user):
    return user.role == 'employee' and user.sub_role == 'faculty'

def is_teacher(user):
    return user.role == 'employee' and user.sub_role == 'teacher'

def is_other_employee(user):
    return user.role == 'employee' and user.sub_role == 'other'


@login_required
@user_passes_test(is_employee)
def dashboard(request):
    user = request.user
    sub_role = user.sub_role
    
    # Common data for all employees
    recent_activities = AuditLog.objects.filter(user=user).order_by('-created_at')[:10]
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    context = {
        'recent_activities': recent_activities,
        'unread_notifications': unread_notifications,
    }
    
    # Role-specific data
    if sub_role == 'hr':
        return hr_dashboard(request, context)
    elif sub_role == 'finance':
        return finance_dashboard(request, context)
    elif sub_role == 'faculty':
        return faculty_dashboard(request, context)
    elif sub_role == 'teacher':
        return teacher_dashboard(request, context)
    else:
        return other_dashboard(request, context)


def hr_dashboard(request, context):
    # HR specific data
    total_employees = User.objects.filter(role='employee').count()
    active_job_posts = JobPost.objects.filter(is_active=True).count()
    pending_applications = Application.objects.filter(status='pending').count()
    scheduled_interviews = InterviewSchedule.objects.filter(status='scheduled').count()
    
    # Recent job posts
    recent_job_posts = JobPost.objects.filter(posted_by=request.user).order_by('-created_at')[:5]
    
    # Recent applications
    recent_applications = Application.objects.all().order_by('-applied_at')[:5]
    
    # Upcoming interviews
    upcoming_interviews = InterviewSchedule.objects.filter(
        scheduled_date__gte=timezone.now()
    ).order_by('scheduled_date')[:5]
    
    context.update({
        'total_employees': total_employees,
        'active_job_posts': active_job_posts,
        'pending_applications': pending_applications,
        'scheduled_interviews': scheduled_interviews,
        'recent_job_posts': recent_job_posts,
        'recent_applications': recent_applications,
        'upcoming_interviews': upcoming_interviews,
        'active_page': 'dashboard',
    })
    
    return render(request, 'EmployeeApp/hr_dashboard.html', context)


def finance_dashboard(request, context):
    # Finance specific data
    pending_salaries = Salary.objects.filter(status='pending').count()
    pending_expenses = Expense.objects.filter(status='pending').count()
    
    # Current month financial overview
    current_month = timezone.now().date().replace(day=1)
    current_month_salaries = Salary.objects.filter(month=current_month)
    current_month_expenses = Expense.objects.filter(date__year=current_month.year, date__month=current_month.month)
    
    total_salaries = current_month_salaries.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = current_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent transactions
    recent_transactions = Transaction.objects.all().order_by('-date')[:10]
    
    # Recent salaries
    recent_salaries = Salary.objects.all().order_by('-created_at')[:10]
    
    # Recent expenses
    recent_expenses = Expense.objects.all().order_by('-date')[:10]
    
    context.update({
        'pending_salaries': pending_salaries,
        'pending_expenses': pending_expenses,
        'total_salaries': total_salaries,
        'total_expenses': total_expenses,
        'recent_transactions': recent_transactions,
        'recent_salaries': recent_salaries,
        'recent_expenses': recent_expenses,
        'active_page': 'dashboard',
    })
    
    return render(request, 'EmployeeApp/finance_dashboard.html', context)


def faculty_dashboard(request, context):
    # Faculty specific data
    total_teachers = User.objects.filter(role='employee', sub_role='teacher').count()
    total_students = User.objects.filter(role='student').count()
    active_courses = Course.objects.filter(status='active').count()
    pending_requests = Course.objects.filter(status='pending_approval').count()
    
    # Recent courses
    recent_courses = Course.objects.all().order_by('-created_at')[:5]
    
    # Pending course requests
    pending_courses = Course.objects.filter(status='pending_approval').order_by('-created_at')[:5]
    
    context.update({
        'total_teachers': total_teachers,
        'total_students': total_students,
        'active_courses': active_courses,
        'pending_requests': pending_requests,
        'recent_courses': recent_courses,
        'pending_courses': pending_courses,
        'active_page': 'dashboard',
    })
    
    return render(request, 'EmployeeApp/faculty_dashboard.html', context)


def teacher_dashboard(request, context):
    # Teacher specific data
    teacher = request.user
    active_courses = CourseTeacher.objects.filter(teacher=teacher, course__status='active').count()
    total_students = Enrollment.objects.filter(course__teachers__teacher=teacher).count()
    pending_tasks = Assignment.objects.filter(course__teachers__teacher=teacher, due_date__gte=timezone.now()).count()
    
    # Classes this week
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    classes_this_week = ClassRoutine.objects.filter(
        teacher=teacher,
        is_active=True
    ).count()
    
    # Today's schedule
    today_routines = ClassRoutine.objects.filter(
        teacher=teacher,
        day_of_week=today.strftime('%A').lower(),
        is_active=True
    ).order_by('start_time')
    
    # Pending tasks
    pending_assignments = Assignment.objects.filter(
        course__teachers__teacher=teacher,
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]
    
    context.update({
        'active_courses': active_courses,
        'total_students': total_students,
        'pending_tasks': pending_tasks,
        'classes_this_week': classes_this_week,
        'today_routines': today_routines,
        'pending_assignments': pending_assignments,
        'active_page': 'dashboard',
    })
    
    return render(request, 'EmployeeApp/teacher_dashboard.html', context)


def other_dashboard(request, context):
    # Other roles (Librarian, Security Guard, Guest Lecturer, etc.)
    user = request.user
    
    # Today's attendance status
    today = timezone.now().date()
    try:
        attendance = Attendance.objects.get(user=user, date=today)
        attendance_status = attendance.status
    except Attendance.DoesNotExist:
        attendance_status = None
    
    # Monthly attendance
    current_month = today.replace(day=1)
    monthly_attendance = Attendance.objects.filter(
        user=user,
        date__gte=current_month,
        date__lte=today
    ).count()
    
    # Present days this month
    present_days = Attendance.objects.filter(
        user=user,
        date__gte=current_month,
        date__lte=today,
        status='present'
    ).count()
    
    context.update({
        'attendance_status': attendance_status,
        'monthly_attendance': monthly_attendance,
        'present_days': present_days,
        'active_page': 'dashboard',
    })
    
    return render(request, 'EmployeeApp/other_dashboard.html', context)


# HR Views
@login_required
@user_passes_test(is_hr)
def job_posts(request):
    job_posts_list = JobPost.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'active':
            job_posts_list = job_posts_list.filter(is_active=True)
        elif status_filter == 'inactive':
            job_posts_list = job_posts_list.filter(is_active=False)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        job_posts_list = job_posts_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(role__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(job_posts_list, 10)  # Show 10 job posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'active_page': 'job_posts',
    }
    return render(request, 'EmployeeApp/job_posts.html', context)


@login_required
@user_passes_test(is_hr)
def create_job_post(request):
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job_post = form.save(commit=False)
            job_post.posted_by = request.user
            job_post.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created job post: {job_post.title}",
                model_name="JobPost",
                object_id=str(job_post.id)
            )
            
            messages.success(request, f'Job post {job_post.title} created successfully')
            return redirect('employee:job_posts')
    else:
        form = JobPostForm()
    
    context = {
        'form': form,
        'title': 'Create Job Post',
        'active_page': 'job_posts',
    }
    return render(request, 'EmployeeApp/job_post_form.html', context)


@login_required
@user_passes_test(is_hr)
def applications(request):
    applications_list = Application.objects.all().order_by('-applied_at')
    
    # Filter by job post
    job_filter = request.GET.get('job')
    if job_filter:
        applications_list = applications_list.filter(job_id=job_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications_list = applications_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications_list, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all job posts for filter dropdown
    job_posts = JobPost.objects.all().order_by('title')
    
    context = {
        'page_obj': page_obj,
        'job_filter': job_filter,
        'status_filter': status_filter,
        'job_posts': job_posts,
        'active_page': 'applications',
    }
    return render(request, 'EmployeeApp/applications.html', context)


# Finance Views
@login_required
@user_passes_test(is_finance)
def salaries(request):
    salaries_list = Salary.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        salaries_list = salaries_list.filter(status=status_filter)
    
    # Filter by month
    month_filter = request.GET.get('month')
    if month_filter:
        try:
            filter_month = parse_date(month_filter + '-01')
            if filter_month:
                salaries_list = salaries_list.filter(month=filter_month)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(salaries_list, 10)  # Show 10 salaries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'month_filter': month_filter,
        'active_page': 'salaries',
    }
    return render(request, 'EmployeeApp/salaries.html', context)


@login_required
@user_passes_test(is_finance)
def expenses(request):
    expenses_list = Expense.objects.all().order_by('-date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        expenses_list = expenses_list.filter(status=status_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        expenses_list = expenses_list.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(expenses_list, 10)  # Show 10 expenses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'active_page': 'expenses',
    }
    return render(request, 'EmployeeApp/expenses.html', context)


# Faculty Views
@login_required
@user_passes_test(is_faculty)
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
        'active_page': 'faculty_courses',
    }
    return render(request, 'EmployeeApp/faculty_courses.html', context)


@login_required
@user_passes_test(is_faculty)
def requests(request):
    # Get pending course requests
    pending_courses = Course.objects.filter(status='pending_approval').order_by('-created_at')
    
    # Get pending teacher applications
    pending_teachers = Application.objects.filter(
        status='accepted',
        job__role='teacher'
    ).order_by('-applied_at')
    
    context = {
        'pending_courses': pending_courses,
        'pending_teachers': pending_teachers,
        'active_page': 'requests',
    }
    return render(request, 'EmployeeApp/requests.html', context)


# Teacher Views
@login_required
@user_passes_test(is_teacher)
def class_routine(request):
    teacher = request.user
    
    # Get class routines for this teacher
    routines = ClassRoutine.objects.filter(teacher=teacher).order_by('day_of_week', 'start_time')
    
    # Group by day of week
    routines_by_day = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        routines_by_day[day] = routines.filter(day_of_week=day)
    
    context = {
        'routines_by_day': routines_by_day,
        'active_page': 'class_routine',
    }
    return render(request, 'EmployeeApp/class_routine.html', context)


@login_required
@user_passes_test(is_teacher)
def create_class_routine(request):
    teacher = request.user
    
    if request.method == 'POST':
        form = ClassRoutineForm(request.POST)
        if form.is_valid():
            routine = form.save(commit=False)
            routine.teacher = teacher
            routine.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created class routine: {routine.course.title} on {routine.day_of_week}",
                model_name="ClassRoutine",
                object_id=str(routine.id)
            )
            
            messages.success(request, f'Class routine for {routine.course.title} on {routine.day_of_week} created successfully')
            return redirect('employee:class_routine')
    else:
        form = ClassRoutineForm()
        # Filter courses to only show courses this teacher teaches
        form.fields['course'].queryset = Course.objects.filter(teachers__teacher=teacher)
    
    context = {
        'form': form,
        'title': 'Create Class Routine',
        'active_page': 'class_routine',
    }
    return render(request, 'EmployeeApp/class_routine_form.html', context)


@login_required
@user_passes_test(is_teacher)
def attendance(request):
    teacher = request.user
    
    # Get attendance records for courses taught by this teacher
    attendance_list = Attendance.objects.filter(
        user__enrollments__course__teachers__teacher=teacher
    ).distinct().order_by('-date')
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            parsed_date = parse_date(date_filter)
            if parsed_date:
                attendance_list = attendance_list.filter(date=parsed_date)
        except ValueError:
            pass
    
    # Filter by course
    course_filter = request.GET.get('course')
    if course_filter:
        attendance_list = attendance_list.filter(
            user__enrollments__course_id=course_filter
        ).distinct()
    
    # Pagination
    paginator = Paginator(attendance_list, 20)  # Show 20 attendance records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get courses taught by this teacher for filter dropdown
    courses = Course.objects.filter(teachers__teacher=teacher)
    
    context = {
        'page_obj': page_obj,
        'date_filter': date_filter,
        'course_filter': course_filter,
        'courses': courses,
        'active_page': 'teacher_attendance',
    }
    return render(request, 'EmployeeApp/teacher_attendance.html', context)


@login_required
@user_passes_test(is_teacher)
def take_attendance(request):
    teacher = request.user
    today = timezone.now().date()
    
    # Get courses taught by this teacher today
    today_day = today.strftime('%A').lower()
    today_routines = ClassRoutine.objects.filter(
        teacher=teacher,
        day_of_week=today_day,
        is_active=True
    ).order_by('start_time')
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        course = get_object_or_404(Course, pk=course_id, teachers__teacher=teacher)
        
        # Get students enrolled in this course
        enrollments = Enrollment.objects.filter(course=course, status='ongoing')
        
        # Process attendance for each student
        for enrollment in enrollments:
            student = enrollment.student
            status = request.POST.get(f'attendance_{student.id}')
            
            # Create or update attendance record
            attendance, created = Attendance.objects.get_or_create(
                user=student,
                date=today,
                defaults={
                    'status': status or 'present',
                    'marked_by': teacher
                }
            )
            
            if not created:
                attendance.status = status or 'present'
                attendance.marked_by = teacher
                attendance.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=f"Marked attendance for course: {course.title}",
            model_name="Attendance",
            object_id=str(course.id)
        )
        
        messages.success(request, f'Attendance for {course.title} marked successfully')
        return redirect('employee:take_attendance')
    
    context = {
        'today_routines': today_routines,
        'active_page': 'teacher_attendance',
    }
    return render(request, 'EmployeeApp/take_attendance.html', context)


@login_required
@user_passes_test(is_teacher)
def lesson_plan(request):
    teacher = request.user
    
    # Get lesson plans for courses taught by this teacher
    lesson_plans = LessonPlan.objects.filter(
        course__teachers__teacher=teacher
    ).order_by('-date')
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            parsed_date = parse_date(date_filter)
            if parsed_date:
                lesson_plans = lesson_plans.filter(date=parsed_date)
        except ValueError:
            pass
    
    # Filter by course
    course_filter = request.GET.get('course')
    if course_filter:
        lesson_plans = lesson_plans.filter(course_id=course_filter)
    
    # Pagination
    paginator = Paginator(lesson_plans, 10)  # Show 10 lesson plans per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get courses taught by this teacher for filter dropdown
    courses = Course.objects.filter(teachers__teacher=teacher)
    
    context = {
        'page_obj': page_obj,
        'date_filter': date_filter,
        'course_filter': course_filter,
        'courses': courses,
        'active_page': 'lesson_plan',
    }
    return render(request, 'EmployeeApp/lesson_plan.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_courses(request):
    teacher = request.user
    
    # Get courses taught by this teacher
    courses_list = Course.objects.filter(teachers__teacher=teacher).order_by('title')
    
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
        'active_page': 'teacher_courses',
    }
    return render(request, 'EmployeeApp/teacher_courses.html', context)


@login_required
@user_passes_test(is_teacher)
def create_teacher_course(request):
    teacher = request.user
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = teacher
            course.status = 'pending_approval'  # Teacher created courses need approval
            course.save()
            
            # Automatically assign this teacher as primary teacher
            CourseTeacher.objects.create(
                course=course,
                teacher=teacher,
                is_primary=True,
                assigned_by=teacher
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Created course: {course.title}",
                model_name="Course",
                object_id=str(course.id)
            )
            
            messages.success(request, f'Course {course.title} created successfully and sent for approval')
            return redirect('employee:teacher_courses')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Create Course',
        'active_page': 'teacher_courses',
    }
    return render(request, 'EmployeeApp/course_form.html', context)


@login_required
@user_passes_test(is_teacher)
def assignments(request):
    teacher = request.user
    
    # Get assignments for courses taught by this teacher
    assignments_list = Assignment.objects.filter(
        course__teachers__teacher=teacher
    ).order_by('-due_date')
    
    # Filter by course
    course_filter = request.GET.get('course')
    if course_filter:
        assignments_list = assignments_list.filter(course_id=course_filter)
    
    # Pagination
    paginator = Paginator(assignments_list, 10)  # Show 10 assignments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get courses taught by this teacher for filter dropdown
    courses = Course.objects.filter(teachers__teacher=teacher)
    
    context = {
        'page_obj': page_obj,
        'course_filter': course_filter,
        'courses': courses,
        'active_page': 'assignments',
    }
    return render(request, 'EmployeeApp/assignments.html', context)


# Other Employee Views (for roles like Librarian, Security Guard, etc.)
@login_required
@user_passes_test(is_other_employee)
def mark_attendance(request):
    user = request.user
    today = timezone.now().date()
    
    # Check if attendance for today already exists
    try:
        attendance = Attendance.objects.get(user=user, date=today)
        messages.info(request, f'You have already marked your attendance for today as {attendance.status}')
        return redirect('employee:dashboard')
    except Attendance.DoesNotExist:
        pass
    
    if request.method == 'POST':
        status = request.POST.get('status', 'present')
        
        # Create attendance record
        attendance = Attendance.objects.create(
            user=user,
            date=today,
            status=status,
            check_in_time=timezone.now().time()
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=f"Marked attendance as {status}",
            model_name="Attendance",
            object_id=str(attendance.id)
        )
        
        messages.success(request, f'Attendance marked as {status} successfully')
        return redirect('employee:dashboard')
    
    context = {
        'active_page': 'attendance',
    }
    return render(request, 'EmployeeApp/mark_attendance.html', context)