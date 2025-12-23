# chat/urls.py - WITHOUT NAMESPACE
from django.urls import path
from . import views

# REMOVE: app_name = 'chat'  # Remove this line

urlpatterns = [
    # Chat home and main pages
    path('', views.chat_home, name='chat_home'),
    path('home/', views.chat_home, name='chat_home_alt'),

    # Conversations
    path('conversation/<uuid:conversation_id>/', views.conversation, name='conversation'),
    path('start-chat/', views.start_chat, name='start_chat'),
    path('quick-chat/<int:user_id>/', views.quick_chat, name='quick_chat'),

    # Groups
    path('create-group/', views.create_group, name='create_group'),
    path('group/', views.group_chat, name='group_chat'),
    path('group/<uuid:conversation_id>/', views.group_chat, name='group_chat_view'),
    path('group/<uuid:conversation_id>/settings/', views.group_settings, name='group_settings'),
    path('group/<uuid:conversation_id>/leave/', views.leave_group, name='leave_group'),
    path('group/<uuid:conversation_id>/invite/', views.invite_to_group, name='invite_to_group'),

    # Messages
    path('send-message/<uuid:conversation_id>/', views.send_message_ajax, name='send_message_ajax'),
    path('get-messages/<uuid:conversation_id>/', views.get_messages_ajax, name='get_messages_ajax'),
    path('get-new-messages/<uuid:conversation_id>/', views.get_new_messages, name='get_new_messages'),

    # Typing indicators
    path('typing/<uuid:conversation_id>/', views.typing_indicator, name='typing_indicator'),
    path('typing-status/<uuid:conversation_id>/', views.get_typing_status, name='get_typing_status'),
    path('typing-ws/<uuid:conversation_id>/', views.typing_status_ws, name='typing_status_ws'),

    # Online status - FIX THIS VIEW
    path('update-online-status/', views.update_online_status, name='update_online_status'),

    # Discover and search users
    path('discover/', views.discover_users, name='discover_users'),
    path('search-users/', views.search_users, name='search_users'),

    # Block users
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('blocked-users/', views.blocked_users, name='blocked_users'),

    # Video/Audio chat
    path('video-chat/<uuid:conversation_id>/', views.video_chat, name='video_chat'),
    path('audio-chat/<uuid:conversation_id>/', views.audio_chat, name='audio_chat'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications_chat'),

    # Edit/Delete messages
    path('edit-message/<uuid:message_id>/', views.edit_message, name='edit_message'),
    path('unsend-message/<uuid:message_id>/', views.unsend_message, name='unsend_message'),
    path('react-to-message/<uuid:message_id>/', views.react_to_message, name='react_to_message'),

    # Conversation management
    path('delete-conversation/<uuid:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('restore-conversation/<uuid:conversation_id>/', views.restore_conversation, name='restore_conversation'),
    path('archived-conversations/', views.archived_conversations, name='archived_conversations'),
    path('clear-conversation/<uuid:conversation_id>/', views.clear_conversation, name='clear_conversation'),

    # Search
    path('search/', views.message_search, name='message_search'),
    path('search/<uuid:conversation_id>/', views.message_search, name='conversation_message_search'),
]