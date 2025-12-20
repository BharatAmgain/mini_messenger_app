# messenger/context_processors.py
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def site_info(request):
    """Add site information to all templates - ENHANCED FOR MOBILE"""
    try:
        current_site = get_current_site(request)

        context = {
            'SITE_NAME': settings.SITE_NAME,
            'SITE_DOMAIN': settings.SITE_DOMAIN or current_site.domain,
            'ADMIN_EMAIL': settings.ADMIN_EMAIL,
            'SUPPORT_EMAIL': settings.SUPPORT_EMAIL,
            'DEBUG': settings.DEBUG,
            'ENABLE_SOCIAL_AUTH': settings.ENABLE_SOCIAL_AUTH,
            'ENABLE_TWO_FACTOR': settings.ENABLE_TWO_FACTOR,
        }

        # Safely add user info
        if request.user.is_authenticated:
            try:
                context['user_has_profile_picture'] = bool(
                    request.user.profile_picture and
                    hasattr(request.user.profile_picture, 'url') and
                    request.user.profile_picture.url
                )
                context['user_email'] = request.user.email or ''
                context['user_username'] = request.user.username or ''
                context['user_first_name'] = request.user.first_name or ''
                context['user_last_name'] = request.user.last_name or ''
                context['user_is_verified'] = getattr(request.user, 'is_verified', False)
                context['user_phone_number'] = getattr(request.user, 'phone_number', '')

                # Check if user is online
                try:
                    from accounts.models import UserStatus
                    status = UserStatus.objects.get(user=request.user)
                    context['user_is_online'] = status.online
                    context['user_last_seen'] = status.last_seen
                except:
                    context['user_is_online'] = False
                    context['user_last_seen'] = None

            except Exception as e:
                # Fallback if any user attribute access fails
                context['user_has_profile_picture'] = False
                context['user_email'] = ''
                context['user_username'] = ''
                context['user_first_name'] = ''
                context['user_last_name'] = ''
                context['user_is_verified'] = False
                context['user_phone_number'] = ''
                context['user_is_online'] = False
                context['user_last_seen'] = None
        else:
            context['user_has_profile_picture'] = False
            context['user_email'] = ''
            context['user_username'] = ''
            context['user_first_name'] = ''
            context['user_last_name'] = ''
            context['user_is_verified'] = False
            context['user_phone_number'] = ''
            context['user_is_online'] = False
            context['user_last_seen'] = None

        # Add current path for active navigation highlighting
        context['current_path'] = request.path

        # Check if it's a mobile device
        context['is_mobile'] = getattr(request, 'is_mobile', False)

        # Add media URL
        context['MEDIA_URL'] = settings.MEDIA_URL

        # Add feature flags
        context['ENABLE_GROUP_CHATS'] = settings.ENABLE_GROUP_CHATS
        context['ENABLE_FILE_UPLOADS'] = settings.ENABLE_FILE_UPLOADS

        # Add CSRF token for forms
        from django.middleware.csrf import get_token
        context['csrf_token'] = get_token(request)

        # Add timezone
        context['TIME_ZONE'] = settings.TIME_ZONE

        return context

    except Exception as e:
        # Minimal safe fallback
        return {
            'SITE_NAME': 'Connect.io',
            'SITE_DOMAIN': 'connect.io',
            'DEBUG': False,
            'is_mobile': False,
            'current_path': request.path if hasattr(request, 'path') else '/',
        }