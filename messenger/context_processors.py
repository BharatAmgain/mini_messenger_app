# messenger/context_processors.py
from django.conf import settings


def site_info(request):
    """Add site information to all templates - FIXED VERSION"""
    context = {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'ADMIN_EMAIL': settings.ADMIN_EMAIL,
        'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
        'DEBUG': settings.DEBUG,
    }

    # Safely add user info without causing template errors
    if request.user.is_authenticated:
        context['user_has_profile_picture'] = bool(request.user.profile_picture)
        context['user_email'] = request.user.email
        context['user_username'] = request.user.username
    else:
        context['user_has_profile_picture'] = False
        context['user_email'] = ''
        context['user_username'] = ''

    # Add current path for active navigation highlighting
    context['current_path'] = request.path

    return context