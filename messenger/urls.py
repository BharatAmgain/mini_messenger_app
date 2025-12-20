# messenger/urls.py - FIXED VERSION
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


def health_check(request):
    """Health check endpoint for Render"""
    from django.http import JsonResponse
    return JsonResponse({"status": "ok", "service": "messenger-app", "version": "1.0.0"})


urlpatterns = [
    # Health check endpoint (must come first for Render monitoring)
    path('health/', health_check, name='health_check'),

    # Admin site
    path('admin/', admin.site.urls),

    # Accounts app URLs
    path('accounts/', include('accounts.urls')),

    # ✅ FIXED: Only ONE social auth URL pattern
    # Choose ONE of these options:

    # OPTION 1: Using 'accounts/' (Recommended - keeps all auth under /accounts/)
    path('accounts/', include('social_django.urls', namespace='social')),

    # OR OPTION 2: Using 'oauth/' (Alternative)
    # path('oauth/', include('social_django.urls', namespace='social')),

    # Chat app URLs
    path('chat/', include('chat.urls')),

    # Redirect root to chat home
    path('', RedirectView.as_view(pattern_name='chat_home', permanent=False)),

    # Legal pages
    path('privacy-policy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='terms_of_service.html'), name='terms_of_service'),
    path('data-deletion/', TemplateView.as_view(template_name='data_deletion.html'), name='data_deletion'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Debug information
if settings.DEBUG:
    print("\n" + "=" * 60)
    print("URL CONFIGURATION")
    print("=" * 60)
    print(f"Social Auth URL: accounts/social/")
    print(f"Media URL: {settings.MEDIA_URL}")
    print("=" * 60)