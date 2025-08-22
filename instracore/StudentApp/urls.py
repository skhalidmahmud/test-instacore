from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('academics/', views.academics, name='academics'),
    path('attendance/', views.attendance_detail, name='attendance_detail'),
    path('exam-results/', views.exam_results, name='exam_results'),
    path('finance/', views.finance, name='finance'),
    path('resources/', views.resources, name='resources'),
    path('certificates/', views.certificates, name='certificates'),
    path('certificates/apply/', views.apply_certificate, name='apply_certificate'),
    path('courses/', views.courses, name='courses'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
]