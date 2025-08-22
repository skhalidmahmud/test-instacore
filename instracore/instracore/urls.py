from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('AuthApp.urls')),
    path('dashboard/admin/', include('AdminApp.urls', namespace='admin_dashboard')),
    path('employee/', include('EmployeeApp.urls')),
    path('student/', include('StudentApp.urls')),
    path('candidate/', include('CandidateApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)