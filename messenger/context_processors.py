# messenger/context_processors.py
from django.conf import settings


def site_info(request):
    """Add site information to all templates"""
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'DEBUG': settings.DEBUG,
    }