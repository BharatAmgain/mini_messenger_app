# messenger_app/chat/templatetags/chat_filters.py
from django import template
from chat.models import Conversation

register = template.Library()

@register.filter
def get_conversation(user, current_user):
    """Get existing conversation between two users"""
    try:
        conversation = Conversation.objects.filter(
            participants=current_user
        ).filter(
            participants=user
        ).filter(
            is_group=False
        ).first()
        return conversation
    except:
        return None

@register.filter
def split(value, key):
    """Split a string by the given key"""
    return value.split(key)

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key, 0)