# chat/routing.py - WebSocket URL routing
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket for real-time messaging
    re_path(r'ws/chat/(?P<conversation_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),

    # User status WebSocket for online/offline tracking
    re_path(r'ws/status/$', consumers.UserStatusConsumer.as_asgi()),

    # Call WebSocket for audio/video calls
    re_path(r'ws/call/$', consumers.CallConsumer.as_asgi()),
]