from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
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
from EmployeeApp.models import Course, Attendance, ClassRoutine
from StudentApp.models import Enrollment, ExamResult, Certificate, GuardianReport, FeePayment
from StudentApp.forms import (
    EnrollmentForm, ExamResultForm, CertificateForm, GuardianReportForm, FeePaymentForm
)


def is_student(user):
    return user.role == 'student'


@login_required
@user_passes_test(is_student)
def dashboard(request):
    student = request.user
    
    # Get active courses
    active_enrollments = Enrollment.objects.filter(student=student, status='ongoing')
    active_courses = active_enrollments.count()
    
    # Get certificates
    certificates = Certificate.objects.filter(student=student)
    earned_certificates = certificates.filter(status='issued').count()
    pending_certificates = certificates.filter(status='pending').count()
    
    # Get unpaid fees
    unpaid_fees = FeePayment.objects.filter(
        enrollment__student=student,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get upcoming classes
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    upcoming_classes = ClassRoutine.objects.filter(
        course__enrollments__student=student,
        course__enrollments__status='ongoing',
        date__gte=today,
        date__lte=end_of_week
    ).order_by('date', 'start_time')[:5]
    
    # Get recent results
    recent_results = ExamResult.objects.filter(
        enrollment__student=student
    ).order_by('-created_at')[:5]
    
    # Get my courses
    my_courses = Enrollment.objects.filter(
        student=student,
        status__in=['ongoing', 'completed']
    ).order_by('-enrolled_at')[:5]
    
    context = {
        'active_courses': active_courses,
        'earned_certificates': earned_certificates,
        'pending_certificates': pending_certificates,
        'unpaid_fees': unpaid_fees,
        'upcoming_classes': upcoming_classes,
        'recent_results': recent_results,
        'my_courses': my_courses,
        'active_page': 'dashboard',
    }
    return render(request, 'StudentApp/dashboard.html', context)


@login_required
@user_passes_test(is_student)
def academics(request):
    student = request.user
    
    # Get attendance data
    attendance_records = Attendance.objects.filter(user=student)
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='present').count()
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get exam results
    exam_results = ExamResult.objects.filter(enrollment__student=student)
    total_exams = exam_results.count()
    passed_exams = exam_results.filter(passed=True).count()
    pass_rate = (passed_exams / total_exams * 100) if total_exams > 0 else 0
    
    # Get average marks
    avg_marks = exam_results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
    
    # Get class schedule
    today = timezone.now().date()
    class_schedules = ClassRoutine.objects.filter(
        course__enrollments__student=student,
        course__enrollments__status='ongoing'
    ).order_by('day_of_week', 'start_time')
    
    # Group by day of week
    schedules_by_day = {}
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        schedules_by_day[day] = class_schedules.filter(day_of_week=day)
    
    # Get leave status
    leave_records = attendance_records.filter(status='leave').order_by('-date')[:5]
    
    context = {
        'attendance_rate': attendance_rate,
        'pass_rate': pass_rate,
        'avg_marks': avg_marks,
        'schedules_by_day': schedules_by_day,
        'leave_records': leave_records,
        'active_page': 'academics',
    }
    return render(request, 'StudentApp/academics.html', context)


@login_required
@user_passes_test(is_student)
def attendance_detail(request):
    student = request.user
    
    # Get attendance records
    attendance_list = Attendance.objects.filter(user=student).order_by('-date')
    
    # Filter by month
    month_filter = request.GET.get('month')
    if month_filter:
        try:
            filter_month = parse_date(month_filter + '-01')
            if filter_month:
                attendance_list = attendance_list.filter(
                    date__year=filter_month.year,
                    date__month=filter_month.month
                )
        except ValueError:
            pass
    
    # Calculate attendance statistics
    total_days = attendance_list.count()
    present_days = attendance_list.filter(status='present').count()
    absent_days = attendance_list.filter(status='absent').count()
    leave_days = attendance_list.filter(status='leave').count()
    late_days = attendance_list.filter(status='late').count()
    
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Pagination
    paginator = Paginator(attendance_list, 20)  # Show 20 attendance records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'month_filter': month_filter,
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'late_days': late_days,
        'attendance_rate': attendance_rate,
        'active_page': 'academics',
    }
    return render(request, 'StudentApp/attendance_detail.html', context)


@login_required
@user_passes_test(is_student)
def exam_results(request):
    student = request.user
    
    # Get exam results
    results_list = ExamResult.objects.filter(enrollment__student=student).order_by('-created_at')
    
    # Filter by course
    course_filter = request.GET.get('course')
    if course_filter:
        results_list = results_list.filter(enrollment__course_id=course_filter)
    
    # Pagination
    paginator = Paginator(results_list, 10)  # Show 10 results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get courses for filter dropdown
    courses = Course.objects.filter(enrollments__student=student).distinct()
    
    context = {
        'page_obj': page_obj,
        'course_filter': course_filter,
        'courses': courses,
        'active_page': 'academics',
    }
    return render(request, 'StudentApp/exam_results.html', context)


@login_required
@user_passes_test(is_student)
def finance(request):
    student = request.user
    
    # Get fee payments
    fee_payments = FeePayment.objects.filter(
        enrollment__student=student
    ).order_by('due_date')
    
    # Calculate totals
    total_fees = fee_payments.aggregate(total=Sum('amount'))['total'] or 0
    paid_fees = fee_payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    unpaid_fees = fee_payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    
    # Get upcoming payments
    upcoming_payments = fee_payments.filter(
        status='pending',
        due_date__gte=timezone.now().date()
    ).order_by('due_date')[:5]
    
    # Get payment history
    payment_history = fee_payments.filter(status='paid').order_by('-paid_at')[:10]
    
    context = {
        'total_fees': total_fees,
        'paid_fees': paid_fees,
        'unpaid_fees': unpaid_fees,
        'upcoming_payments': upcoming_payments,
        'payment_history': payment_history,
        'active_page': 'finance',
    }
    return render(request, 'StudentApp/finance.html', context)


@login_required
@user_passes_test(is_student)
def resources(request):
    student = request.user
    
    # Get enrolled courses
    enrollments = Enrollment.objects.filter(
        student=student,
        status__in=['ongoing', 'completed']
    )
    
    # Get syllabi for enrolled courses
    syllabi = []
    for enrollment in enrollments:
        if enrollment.course.syllabus:
            syllabi.append({
                'course': enrollment.course,
                'syllabus': enrollment.course.syllabus,
            })
    
    context = {
        'syllabi': syllabi,
        'active_page': 'resources',
    }
    return render(request, 'StudentApp/resources.html', context)


@login_required
@user_passes_test(is_student)
def certificates(request):
    student = request.user
    
    # Get certificates
    certificates_list = Certificate.objects.filter(student=student).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        certificates_list = certificates_list.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        certificates_list = certificates_list.filter(certificate_type=type_filter)
    
    # Pagination
    paginator = Paginator(certificates_list, 10)  # Show 10 certificates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get completed courses for certificate application
    completed_enrollments = Enrollment.objects.filter(
        student=student,
        status='completed'
    )
    
    # Get courses that don't have a certificate yet
    courses_without_certificate = []
    for enrollment in completed_enrollments:
        if not Certificate.objects.filter(student=student, course=enrollment.course).exists():
            courses_without_certificate.append(enrollment.course)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'courses_without_certificate': courses_without_certificate,
        'active_page': 'student_certificates',
    }
    return render(request, 'StudentApp/certificates.html', context)


@login_required
@user_passes_test(is_student)
def apply_certificate(request):
    student = request.user
    
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.student = student
            
            # Check if the student has completed the course
            enrollment = Enrollment.objects.get(
                student=student,
                course=certificate.course,
                status='completed'
            )
            
            # Set certificate type based on course type
            if certificate.course.course_type == 'online':
                certificate.certificate_type = 'online'
            elif certificate.course.course_type == 'diploma':
                certificate.certificate_type = 'diploma'
            else:
                certificate.certificate_type = 'offline'
            
            certificate.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f"Applied for certificate for course: {certificate.course.title}",
                model_name="Certificate",
                object_id=str(certificate.id)
            )
            
            messages.success(request, f'Certificate application for {certificate.course.title} submitted successfully')
            return redirect('student:certificates')
    else:
        form = CertificateForm()
        # Filter courses to only show courses the student has completed
        completed_enrollments = Enrollment.objects.filter(
            student=student,
            status='completed'
        )
        completed_course_ids = [enrollment.course.id for enrollment in completed_enrollments]
        
        # Exclude courses that already have a certificate
        existing_certificate_course_ids = Certificate.objects.filter(
            student=student
        ).values_list('course_id', flat=True)
        
        available_course_ids = set(completed_course_ids) - set(existing_certificate_course_ids)
        form.fields['course'].queryset = Course.objects.filter(id__in=available_course_ids)
    
    context = {
        'form': form,
        'title': 'Apply for Certificate',
        'active_page': 'student_certificates',
    }
    return render(request, 'StudentApp/certificate_form.html', context)


@login_required
@user_passes_test(is_student)
def courses(request):
    student = request.user
    
    # Get course type filter
    course_type_filter = request.GET.get('type')
    
    # Get available courses
    available_courses = Course.objects.filter(status='active')
    
    if course_type_filter:
        available_courses = available_courses.filter(course_type=course_type_filter)
    
    # Exclude courses the student is already enrolled in
    enrolled_course_ids = Enrollment.objects.filter(
        student=student
    ).values_list('course_id', flat=True)
    
    available_courses = available_courses.exclude(id__in=enrolled_course_ids)
    
    # Get my enrollments
    my_enrollments = Enrollment.objects.filter(student=student)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        my_enrollments = my_enrollments.filter(status=status_filter)
    
    my_enrollments = my_enrollments.order_by('-enrolled_at')
    
    # Pagination for available courses
    paginator1 = Paginator(available_courses, 6)  # Show 6 courses per page
    page_number = request.GET.get('page1')
    available_page_obj = paginator1.get_page(page_number)
    
    # Pagination for my enrollments
    paginator2 = Paginator(my_enrollments, 10)  # Show 10 enrollments per page
    page_number = request.GET.get('page2')
    enrollments_page_obj = paginator2.get_page(page_number)
    
    context = {
        'available_page_obj': available_page_obj,
        'enrollments_page_obj': enrollments_page_obj,
        'course_type_filter': course_type_filter,
        'status_filter': status_filter,
        'active_page': 'student_courses',
    }
    return render(request, 'StudentApp/courses.html', context)


@login_required
@user_passes_test(is_student)
def course_detail(request, pk):
    student = request.user
    course = get_object_or_404(Course, pk=pk, status='active')
    
    # Check if student is already enrolled
    try:
        enrollment = Enrollment.objects.get(student=student, course=course)
        is_enrolled = True
    except Enrollment.DoesNotExist:
        enrollment = None
        is_enrolled = False
    
    # Get teachers for this course
    teachers = Course.objects.get(pk=pk).teachers.all()
    
    # Get course syllabus if available
    syllabus = course.syllabus
    
    context = {
        'course': course,
        'teachers': teachers,
        'syllabus': syllabus,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'active_page': 'student_courses',
    }
    return render(request, 'StudentApp/course_detail.html', context)


@login_required
@user_passes_test(is_student)
def enroll_course(request, pk):
    student = request.user
    course = get_object_or_404(Course, pk=pk, status='active')
    
    # Check if student is already enrolled
    if Enrollment.objects.filter(student=student, course=course).exists():
        messages.error(request, 'You are already enrolled in this course')
        return redirect('student:course_detail', pk=course.pk)
    
    if request.method == 'POST':
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            status='pending'
        )
        
        # Create fee payment if course has a price
        if course.price > 0:
            FeePayment.objects.create(
                enrollment=enrollment,
                amount=course.price,
                due_date=timezone.now().date() + timedelta(days=30)  # Due in 30 days
            )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=f"Enrolled in course: {course.title}",
            model_name="Enrollment",
            object_id=str(enrollment.id)
        )
        
        messages.success(request, f'Enrollment in {course.title} submitted successfully')
        return redirect('student:courses')
    
    context = {
        'course': course,
        'active_page': 'student_courses',
    }
    return render(request, 'StudentApp/enroll_course.html', context)