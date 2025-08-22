from django import forms
from django.utils import timezone
from AuthApp.models import User
from EmployeeApp.models import (
    JobPost, Application, InterviewSchedule, Salary, Expense, Transaction,
    Course, CourseTeacher, Assignment, LessonPlan, Attendance, ClassRoutine
)


class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ('title', 'description', 'role', 'min_requirements', 'salary_range', 
                  'location', 'language', 'availability', 'application_instructions', 'deadline', 'is_active')
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('resume', 'cover_letter')


class InterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = InterviewSchedule
        fields = ('scheduled_date', 'notes')
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = ('employee', 'amount', 'month', 'status')
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('category', 'amount', 'description', 'date')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('user', 'amount', 'transaction_type', 'description', 'date')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description', 'course_type', 'price', 'duration', 'status', 'syllabus')


class CourseTeacherForm(forms.ModelForm):
    class Meta:
        model = CourseTeacher
        fields = ('teacher', 'is_primary')


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('course', 'title', 'description', 'due_date', 'total_marks')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = ('course', 'title', 'content', 'date')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('user', 'date', 'status', 'check_in_time', 'check_out_time', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ClassRoutineForm(forms.ModelForm):
    class Meta:
        model = ClassRoutine
        fields = ('course', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }