# messenger/views.py
from django.shortcuts import render
from django.http import HttpResponseForbidden

def csrf_failure(request, reason=""):
    """Custom CSRF failure view"""
    context = {
        'title': 'CSRF Verification Failed',
        'message': 'The request could not be processed because a security token was invalid or missing.',
        'reason': reason,
    }
    return render(request, 'errors/csrf_failure.html', context, status=403)