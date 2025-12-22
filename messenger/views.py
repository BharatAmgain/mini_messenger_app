# messenger/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse

def root_redirect(request):
    """Redirect root URL based on authentication status"""
    if request.user.is_authenticated:
        return redirect('chat_home')
    else:
        return redirect('accounts:login')

def home_view(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('chat_home')
    return render(request, 'home.html')

# ========== ERROR HANDLERS ==========
def csrf_failure(request, reason=""):
    """CSRF failure view"""
    return render(request, 'errors/csrf_failure.html', {'reason': reason}, status=403)

def bad_request(request, exception=None):
    """400 Bad Request handler"""
    return render(request, 'errors/400.html', status=400)

def permission_denied(request, exception=None):
    """403 Permission Denied handler"""
    return render(request, 'errors/403.html', status=403)

def page_not_found(request, exception=None):
    """404 Page Not Found handler"""
    return render(request, 'errors/404.html', status=404)

def server_error(request):
    """500 Internal Server Error handler"""
    return render(request, 'errors/500.html', status=500)