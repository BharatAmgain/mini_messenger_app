# messenger/urls.py - COMPLETE WORKING VERSION
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Accounts app URLs
    path('accounts/', include('accounts.urls')),

    # Chat app URLs
    path('chat/', include('chat.urls')),

    # Social auth URLs
    path('oauth/', include('social_django.urls', namespace='social')),

    # Admin
    path('admin/', admin.site.urls),

    # Debug/Test URLs
    path('debug-google-oauth/', views.debug_google_oauth, name='debug_google_oauth'),
]

# Error handlers
handler400 = 'messenger.views.bad_request'
handler403 = 'messenger.views.permission_denied'
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)