from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from .models import Notification
import json
from datetime import datetime

User = get_user_model()


def send_notification(user, notification_type, title, message, **kwargs):
    """
    Send a real-time notification to a user
    """
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_conversation=kwargs.get('conversation'),
        related_message=kwargs.get('message')
    )

    # Send via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user.id}',
        {
            'type': 'send_notification',
            'id': notification.id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'conversation_id': kwargs.get('conversation_id'),
            'timestamp': datetime.now().isoformat(),
            'is_read': False
        }
    )

    return notification


def send_contact_request_notification(from_user, to_user):
    """
    Send notification for contact request
    """
    send_notification(
        to_user,
        'contact_request',
        'New Contact Request',
        f'{from_user.username} wants to add you as a contact',
        from_user=from_user
    )


def send_message_notification(user, conversation, message):
    """
    Send notification for new message
    """
    if conversation.is_group:
        title = f"New message in {conversation.group_name}"
    else:
        # Get the other user in the conversation
        other_users = conversation.participants.exclude(id=user.id)
        if other_users.exists():
            title = f"New message from {other_users.first().username}"
        else:
            title = "New message"

    send_notification(
        user,
        'message',
        title,
        message.content[:100],  # First 100 characters
        conversation=conversation,
        message=message,
        conversation_id=conversation.id
    )


def send_call_notification(user, caller, call_type):
    """
    Send notification for missed call
    """
    call_type_text = "video call" if call_type == 'video' else "audio call"
    send_notification(
        user,
        'call',
        'Missed Call',
        f'You missed a {call_type_text} from {caller.username}',
        from_user=caller
    )