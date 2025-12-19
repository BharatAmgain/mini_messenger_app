# messenger/views.py
from django.shortcuts import render
from django.middleware.csrf import get_token
from django.http import JsonResponse


def csrf_failure(request, reason=""):
    """Custom CSRF failure view - FIXED VERSION"""
    # Get CSRF token for the response
    csrf_token = get_token(request)

    # For AJAX requests, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF verification failed',
            'detail': 'CSRF token missing or incorrect',
            'reason': reason,
            'csrf_token': csrf_token
        }, status=403)

    context = {
        'title': 'Security Verification Failed',
        'message': 'The request could not be processed because a security token was invalid or missing.',
        'detail': 'This is usually caused by:',
        'reasons': [
            'Your session expired (logged out)',
            'You submitted a form without proper security tokens',
            'You tried to access the page from a different browser/tab',
            'The page was open for too long without activity'
        ],
        'reason': reason,
        'csrf_token': csrf_token,
        'user': request.user,  # Pass user to template safely
    }
    return render(request, 'errors/csrf_failure.html', context, status=403)


def health_check(request):
    """Simple health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'ok',
        'service': 'Connect.io Messenger',
        'timestamp': 'server_time_placeholder'
    })