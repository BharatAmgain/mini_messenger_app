# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts_views.root_redirect, name='root'),
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),

    # Social Auth - FIXED: Changed path to avoid conflict
    path('social-auth/', include('social_django.urls', namespace='social')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'
handler403 = 'messenger.views.permission_denied'
handler400 = 'messenger.views.bad_request'