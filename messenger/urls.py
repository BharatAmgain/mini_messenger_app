"""
URL configuration for messenger_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Accounts app (your custom auth)
    path('accounts/', include('accounts.urls')),

    # Social auth (Google OAuth)
    path('accounts/', include('social_django.urls', namespace='social')),

    # Chat app
    path('chat/', include('chat.urls')),

    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Legal pages
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),

    # Debug page (for development only)
    path('debug/', TemplateView.as_view(template_name='debug.html'), name='debug'),

    # Django's built-in auth as backup (optional, since you have custom accounts)
    path('auth/', include('django.contrib.auth.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)