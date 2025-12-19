# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from messenger.views import csrf_failure, health_check
from django.views.generic import TemplateView


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
path('accounts/', include('social_django.urls', namespace='social')),
    path('chat/', include('chat.urls')),
path('oauth/', include('social_django.urls', namespace='social')),

    # Redirect root to chat home
    path('', RedirectView.as_view(pattern_name='chat_home', permanent=False)),
    path('privacy-policy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='terms_of_service.html'), name='terms_of_service'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)