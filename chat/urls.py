# chat/urls.py
from django.urls import path
from . import views

# REMOVE OR COMMENT OUT THIS LINE: app_name = 'chat'

urlpatterns = [
    # Chat home
    path('', views.chat_home, name='chat_home'),

    # Conversations
    path('conversation/<uuid:conversation_id>/', views.conversation, name='conversation'),
    path('start-chat/', views.start_chat, name='start_chat'),
    path('quick-chat/<int:user_id>/', views.quick_chat, name='quick_chat'),

    # Groups
    path('create-group/', views.create_group, name='create_group'),
    path('group/<uuid:conversation_id>/settings/', views.group_settings, name='group_settings'),
    path('group/<uuid:conversation_id>/leave/', views.leave_group, name='leave_group'),
    path('group/<uuid:conversation_id>/invite/', views.invite_to_group, name='invite_to_group'),

    # Messages
    path('send-message/<uuid:conversation_id>/', views.send_message_ajax, name='send_message_ajax'),
    path('get-messages/<uuid:conversation_id>/', views.get_messages_ajax, name='get_messages_ajax'),
    path('get-new-messages/<uuid:conversation_id>/', views.get_new_messages, name='get_new_messages'),
    path('edit-message/<uuid:message_id>/', views.edit_message, name='edit_message'),
    path('unsend-message/<uuid:message_id>/', views.unsend_message, name='unsend_message'),
    path('react-to-message/<uuid:message_id>/', views.react_to_message, name='react_to_message'),

    # Typing indicators
    path('typing/<uuid:conversation_id>/', views.typing_indicator, name='typing_indicator'),
    path('typing-status/<uuid:conversation_id>/', views.get_typing_status, name='get_typing_status'),

    # Online status
    path('update-online-status/', views.update_online_status, name='update_online_status'),

    # Discover users
    path('discover/', views.discover_users, name='discover_users_chat'),  # Changed name to avoid conflict
    path('search/', views.search_users, name='search_users'),

    # Block users
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('blocked-users/', views.blocked_users, name='blocked_users'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications_chat'),

    # Emojis
    path('search-emojis/', views.search_emojis, name='search_emojis'),
    path('emoji-categories/', views.get_emoji_categories, name='get_emoji_categories'),
]