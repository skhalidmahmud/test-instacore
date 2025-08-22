from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('setup/', views.setup, name='setup'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Password management
    path('password-change/', views.password_change, name='password_change'),
    path('password-change/done/', views.password_change_done, name='password_change_done'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    
    # Account management
    path('delete-account/', views.delete_account, name='delete_account'),
    path('account-deleted/', views.account_deleted, name='account_deleted'),
    
    # Additional auth pages
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
]