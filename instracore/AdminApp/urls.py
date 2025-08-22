from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:pk>/update/', views.update_user, name='update_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('courses/', views.courses, name='courses'),
    path('attendance/', views.attendance, name='attendance'),
    path('events-notices/', views.events_notices, name='events_notices'),
    path('events/create/', views.create_event, name='create_event'),
    path('notices/create/', views.create_notice, name='create_notice'),
    path('accounts/', views.accounts, name='accounts'),
    path('reports/', views.reports, name='reports'),
]