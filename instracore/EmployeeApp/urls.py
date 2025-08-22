from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # HR URLs
    path('job-posts/', views.job_posts, name='job_posts'),
    path('job-posts/create/', views.create_job_post, name='create_job_post'),
    path('applications/', views.applications, name='applications'),
    
    # Finance URLs
    path('salaries/', views.salaries, name='salaries'),
    path('expenses/', views.expenses, name='expenses'),
    
    # Faculty URLs
    path('faculty-courses/', views.courses, name='faculty_courses'),
    path('requests/', views.requests, name='requests'),
    
    # Teacher URLs
    path('class-routine/', views.class_routine, name='class_routine'),
    path('class-routine/create/', views.create_class_routine, name='create_class_routine'),
    path('attendance/', views.attendance, name='teacher_attendance'),
    path('take-attendance/', views.take_attendance, name='take_attendance'),
    path('lesson-plan/', views.lesson_plan, name='lesson_plan'),
    path('teacher-courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher-courses/create/', views.create_teacher_course, name='create_teacher_course'),
    path('assignments/', views.assignments, name='assignments'),
    
    # Other Employee URLs
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
]