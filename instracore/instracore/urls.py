from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Root URL - serves the index page
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    
    # Admin site
    path('admin/', admin.site.urls),
    
    # Auth app URLs with namespace
    path('auth/', include('AuthApp.urls', namespace='auth')),
    
    # Other app URLs
    # path('admin/', include('AdminApp.urls')),
    # path('employee/', include('EmployeeApp.urls')),
    # path('student/', include('StudentApp.urls')),
    # path('candidate/', include('CandidateApp.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)