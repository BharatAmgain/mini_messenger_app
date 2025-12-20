# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    # Social auth URLs (for Google OAuth)
    path('accounts/', include('social_django.urls', namespace='social')),

    # Chat app
    path('chat/', include('chat.urls')),

    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Terms and Privacy
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),

    # Debug pages (remove in production)
    path('debug/', TemplateView.as_view(template_name='debug.html'), name='debug'),

    # Django default auth URLs (as backup)
    path('auth/', include('django.contrib.auth.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler400 = 'messenger.views.bad_request'
handler403 = 'messenger.views.permission_denied'
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'