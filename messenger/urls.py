"""
URL configuration for messenger_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from . import views

# Custom home view that checks authentication
def home_view(request):
    """Root home page that redirects based on authentication"""
    if request.user.is_authenticated:
        return render(request, 'home.html')
    else:
        return render(request, 'home.html')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Accounts app (your custom auth) - MUST BE BEFORE social auth
    path('accounts/', include('accounts.urls')),

    # Social auth (Google OAuth) - with specific namespace
    path('social/', include('social_django.urls', namespace='social')),  # Changed from 'accounts/' to 'social/'

    # Chat app
    path('chat/', include('chat.urls')),
    # Home page
    path('', home_view, name='home'),

    # Legal pages
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),

    # Debug page (for development only)
    path('debug/', TemplateView.as_view(template_name='debug.html'), name='debug'),
]

# Error handlers
handler400 = 'messenger.views.bad_request'
handler403 = 'messenger.views.permission_denied'
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)