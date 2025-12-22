# messenger/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import RedirectView


# Simple home view
def home_view(request):
    return render(request, 'home.html')


urlpatterns = [
    path('', home_view, name='home'),  # Root URL goes to home.html

    path('admin/', admin.site.urls),

    # Include chat URLs
    path('chat/', include('chat.urls')),

    # Include accounts URLs
    path('accounts/', include('accounts.urls')),

    # Social auth URLs
    path('auth/', include('social_django.urls', namespace='social')),

    # OTP URLs
    path('otp/', include('django_otp.urls')),
]

# Error handlers
handler400 = 'messenger.views.bad_request'
handler403 = 'messenger.views.permission_denied'
handler404 = 'messenger.views.page_not_found'
handler500 = 'messenger.views.server_error'