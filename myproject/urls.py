"""
URL configuration for Banking Messaging System
نظام المراسلات الداخلية للبنك الإسلامي
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main views
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('messaging/', include('messaging.urls')),
    path('security/', include('security.urls')),
    path('workflows/', include('workflows.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
