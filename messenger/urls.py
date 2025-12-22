# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from messenger import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Social Auth
    path('', include('social_django.urls', namespace='social')),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    # Chat app
    path('chat/', include('chat.urls')),

    # Home
    path('', views.home, name='home'),
]

# Error handlers
handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.page_not_found
handler500 = views.server_error

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)