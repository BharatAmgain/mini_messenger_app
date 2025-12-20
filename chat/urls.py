# messenger_app/chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Chat pages
    path('', views.chat_home, name='chat_home'),
    path('start/', views.start_chat, name='start_chat'),
    path('start/<int:user_id>/', views.start_chat_with_user, name='start_chat_with_user'),
    path('create-group/', views.create_group, name='create_group'),
    path('search/', views.search_users, name='search_users'),
    path('discover/', views.discover_users, name='discover_users'),
    path('blocked/', views.blocked_users, name='blocked_users'),

    # Conversation routes (both GET for viewing and POST for sending messages)
    path('<uuid:conversation_id>/', views.conversation, name='conversation'),

    # AJAX endpoints for messaging
    path('<uuid:conversation_id>/send-message/', views.send_message_ajax, name='send_message_ajax'),
    path('<uuid:conversation_id>/get-messages/', views.get_messages_ajax, name='get_messages_ajax'),
    path('<uuid:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),

    # Group management
    path('group/<uuid:conversation_id>/settings/', views.group_settings, name='group_settings'),
    path('group/<uuid:conversation_id>/leave/', views.leave_group, name='leave_group'),
    path('group/<uuid:conversation_id>/invite/', views.invite_to_group, name='invite_to_group'),

    # Message actions
    path('message/<uuid:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<uuid:message_id>/unsend/', views.unsend_message, name='unsend_message'),
    path('message/<uuid:message_id>/react/', views.react_to_message, name='react_to_message'),

    # Real-time features
    path('<uuid:conversation_id>/typing/', views.typing_indicator, name='typing_indicator'),
    path('<uuid:conversation_id>/typing-status/', views.get_typing_status, name='get_typing_status'),
    path('update-online-status/', views.update_online_status, name='update_online_status'),

    # User actions
    path('quick-chat/<int:user_id>/', views.quick_chat, name='quick_chat'),
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Emoji
    path('emojis/search/', views.search_emojis, name='search_emojis'),
    path('emojis/categories/', views.get_emoji_categories, name='get_emoji_categories'),

    # Device info
    path('device-info/', views.device_info, name='device_info'),

    # Conversation management
    path('<uuid:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
]