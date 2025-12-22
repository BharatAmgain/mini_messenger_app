# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Import error handlers
from . import views as error_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Root URL redirects based on auth status
    path('', RedirectView.as_view(pattern_name='accounts:root_redirect'), name='root'),

    # Accounts app (with namespace)
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Chat app (with namespace)
    path('chat/', include('chat.urls', namespace='chat')),

    # Social auth URLs - CRITICAL: Use exact paths from social_django
    path('oauth/', include('social_django.urls', namespace='social')),

    # Django OTP URLs - FIXED: Correct import
    path('otp/', include('django_otp.urls')),

    # Home page for non-authenticated users
    path('home/', error_views.home, name='home'),

    # Google OAuth debug
    path('debug/google-oauth/', error_views.debug_google_oauth, name='debug_google_oauth'),
]

# Error handlers (MUST be at the bottom)
handler400 = error_views.bad_request
handler403 = error_views.permission_denied
handler404 = error_views.page_not_found
handler500 = error_views.server_error

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)