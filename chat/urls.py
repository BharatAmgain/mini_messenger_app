# messenger_app/chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'  # ADD THIS LINE

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('start-chat/', views.start_chat, name='start_chat'),
    path('create-group/', views.create_group, name='create_group'),
    path('search-users/', views.search_users, name='search_users'),
    path('<uuid:conversation_id>/', views.conversation, name='conversation'),
    path('<uuid:conversation_id>/settings/', views.group_settings, name='group_settings'),
    path('<uuid:conversation_id>/invite/', views.invite_to_group, name='invite_to_group'),
    path('<uuid:conversation_id>/leave/', views.leave_group, name='leave_group'),

    # AJAX endpoints
    path('<uuid:conversation_id>/typing/', views.typing_indicator, name='typing_indicator'),
    path('<uuid:conversation_id>/typing-status/', views.get_typing_status, name='get_typing_status'),
    path('<uuid:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('<uuid:conversation_id>/send-message/', views.send_message_ajax, name='send_message_ajax'),
    path('<uuid:conversation_id>/get-messages/', views.get_messages_ajax, name='get_messages_ajax'),
    path('get-notifications/', views.get_notifications, name='get_notifications'),

    # User discovery and blocking URLs
    path('discover-users/', views.discover_users, name='discover_users'),
    path('block-user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('blocked-users/', views.blocked_users, name='blocked_users'),
    path('quick-chat/<int:user_id>/', views.quick_chat, name='quick_chat'),

    # Message action URLs
    path('message/<uuid:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<uuid:message_id>/unsend/', views.unsend_message, name='unsend_message'),
    path('message/<uuid:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('update-online-status/', views.update_online_status, name='update_online_status'),
    path('search-emojis/', views.search_emojis, name='search_emojis'),
    path('get-emoji-categories/', views.get_emoji_categories, name='get_emoji_categories'),
]