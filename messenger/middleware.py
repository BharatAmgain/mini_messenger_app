# messenger/middleware.py
from django.utils.deprecation import MiddlewareMixin
import re
import logging

logger = logging.getLogger(__name__)


class MobileMiddleware(MiddlewareMixin):
    """Middleware to detect mobile devices and optimize responses"""

    def process_request(self, request):
        request.is_mobile = False
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

        # Check for mobile devices in user agent
        mobile_agents = [
            'android', 'iphone', 'ipad', 'ipod', 'blackberry',
            'windows phone', 'webos', 'opera mini', 'iemobile',
            'mobile', 'tablet', 'kindle', 'silk'
        ]

        for agent in mobile_agents:
            if agent in user_agent:
                request.is_mobile = True
                break

        # Check screen width from custom header
        screen_width = request.headers.get('X-Screen-Width', '0')
        if screen_width and int(screen_width) <= 768:
            request.is_mobile = True

        # Check device type header
        device_type = request.headers.get('X-Device-Type', '').lower()
        if device_type in ['mobile', 'phone', 'tablet']:
            request.is_mobile = True

        # Log mobile detection
        if request.is_mobile:
            logger.info(f"Mobile device detected: {user_agent[:100]}",
                        extra={'user': request.user.username if request.user.is_authenticated else 'anonymous',
                               'device': device_type or 'unknown'})

        return None

    def process_response(self, request, response):
        # Add mobile class to body if mobile
        if hasattr(request, 'is_mobile') and request.is_mobile:
            if hasattr(response, 'content') and response.get('Content-Type', '').startswith('text/html'):
                try:
                    content = response.content.decode('utf-8')
                    if '<body' in content:
                        # Add mobile class to body tag
                        content = content.replace('<body', '<body class="mobile-device"')
                        response.content = content.encode('utf-8')
                except UnicodeDecodeError:
                    pass

        # Add mobile info header
        response['X-Is-Mobile'] = str(request.is_mobile).lower()

        return response

    def process_exception(self, request, exception):
        # Log mobile-specific errors
        if hasattr(request, 'is_mobile') and request.is_mobile:
            logger.error(f"Mobile error: {exception}",
                         extra={'user': request.user.username if request.user.is_authenticated else 'anonymous',
                                'path': request.path})
        return None