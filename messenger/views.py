# messenger/views.py - UPDATED VERSION
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    """Home page for non-authenticated users"""
    return render(request, 'home.html')

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})


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

def debug_google_oauth(request):
    """Debug view for Google OAuth"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google OAuth Debug</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>Google OAuth Configuration</h1>
        <p>Google OAuth is configured for production use.</p>
        <p>Redirect URI: https://connect-io-0cql.onrender.com/complete/google-oauth2/</p>
        <p>Make sure this exact URI is added to Google Cloud Console.</p>
    </body>
    </html>
    """)