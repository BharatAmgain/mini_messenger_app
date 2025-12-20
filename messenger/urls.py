# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from messenger.views import csrf_failure, health_check, data_deletion_view, privacy_policy_view, terms_view
from django.views.generic import TemplateView

urlpatterns = [
    # Health check endpoint
    path('health/', health_check, name='health_check'),

    # Admin interface
    path('admin/', admin.site.urls),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    # Social auth - single namespace
    path('oauth/', include('social_django.urls', namespace='social')),

    # Chat app
    path('chat/', include('chat.urls')),

    # Legal pages
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_view, name='terms_of_service'),
    path('data-deletion/', data_deletion_view, name='data_deletion'),

    # Redirect root to chat home if logged in, else to login
    path('', RedirectView.as_view(pattern_name='chat_home'), name='home'),

    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),

    # Robots.txt
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    # Sitemap
    path('sitemap.xml', TemplateView.as_view(template_name='sitemap.xml', content_type='application/xml')),
]

# Error handlers
handler400 = 'messenger.views.bad_request'
handler403 = 'messenger.views.permission_denied'
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns