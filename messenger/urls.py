# messenger/urls.py - MINIMAL WORKING VERSION
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    # Social auth URLs (for Google OAuth)
    path('accounts/', include('social_django.urls', namespace='social')),

    # Home page - redirect to login
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='home'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# REMOVE ALL ERROR HANDLERS (comment them out or delete)
# handler400 = 'messenger.views.bad_request'
# handler403 = 'messenger.views.permission_denied'
# handler404 = 'messenger.views.page_not_found'
# handler500 = 'messenger.views.server_error'