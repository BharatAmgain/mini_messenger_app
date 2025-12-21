# messenger/views.py - COMPLETE VERSION
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from accounts.views import register as accounts_register

# ========== ERROR VIEWS ==========
def csrf_failure(request, reason=""):
    """Custom CSRF failure view"""
    return render(request, 'errors/403.html', status=403)

def page_not_found(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)

def server_error(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)

def permission_denied(request, exception):
    """Custom 403 error page"""
    return render(request, 'errors/403.html', status=403)

def bad_request(request, exception):
    """Custom 400 error page"""
    return render(request, 'errors/400.html', status=400)

# ========== AUTH VIEWS ==========
def login_view(request):
    """Login view"""
    return LoginView.as_view(template_name='accounts/login.html')(request)

def register_view(request):
    """Register view"""
    return accounts_register(request)

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')

# ========== MAIN VIEWS ==========
def home(request):
    """Home page view"""
    return render(request, 'home.html')