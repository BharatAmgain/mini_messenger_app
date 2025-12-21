# messenger/asgi.py
import os
import django

# Set Django settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')

# Configure Django BEFORE importing anything else
django.setup()

# Now import Django/Channels components
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})