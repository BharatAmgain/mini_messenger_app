# chat/urls.py - COMPLETE WITH VOICE MESSAGE AND CALL SUPPORT
from django.urls import path, re_path
from . import views

print("\n" + "=" * 60)
print("CHAT URLS.PY LOADED")
print("=" * 60)

urlpatterns = [
    # Basic pages
    path('', views.chat_home, name='chat_home'),
    path('start/', views.start_chat, name='start_chat'),
    path('create-group/', views.create_group, name='create_group'),
    path('discover/', views.discover_users, name='discover_users'),
    path('blocked/', views.blocked_users, name='blocked_users'),
    path('stats/', views.message_stats, name='message_stats'),
    path('archived/', views.archived_conversations, name='archived_conversations'),
    path('debug-conversations/', views.debug_conversations, name='debug_conversations'),

    # Search
    path('search/', views.message_search, name='message_search'),
    path('search/users/', views.search_users, name='chat_search_users'),

    # Download file
    path('download/<uuid:message_id>/', views.download_file, name='download_file'),

    # User actions
    re_path(r'^block/(?P<user_id>[^/]+)/$', views.block_user, name='block_user'),
    re_path(r'^unblock/(?P<user_id>[^/]+)/$', views.unblock_user, name='unblock_user'),
    re_path(r'^quick-chat/(?P<user_id>[^/]+)/$', views.quick_chat, name='quick_chat'),

    # Emoji
    path('emojis/search/', views.search_emojis, name='search_emojis'),
    path('emojis/categories/', views.get_emoji_categories, name='get_emoji_categories'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),

    # Online status
    path('update-online-status/', views.update_online_status, name='update_online_status'),

    # Group chat
    path('group/<uuid:conversation_id>/', views.group_chat, name='group_chat'),

    # Message actions
    path('message/<uuid:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<uuid:message_id>/unsend/', views.unsend_message, name='unsend_message'),
    path('message/<uuid:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('message/<uuid:message_id>/pin/', views.pin_message, name='pin_message'),
    path('message/<uuid:message_id>/star/', views.star_message, name='star_message'),

    # Voice message specific
    path('voice/upload/', views.upload_voice_message, name='upload_voice_message'),
    path('voice/play/<uuid:message_id>/', views.play_voice_message, name='play_voice_message'),

    # ===== CONVERSATION-SPECIFIC URLS =====
    path('<uuid:conversation_id>/settings/', views.group_settings, name='group_settings'),
    path('<uuid:conversation_id>/leave/', views.leave_group, name='leave_group'),
    path('<uuid:conversation_id>/invite/', views.invite_to_group, name='invite_to_group'),
    path('<uuid:conversation_id>/typing/', views.typing_indicator, name='typing_indicator'),
    path('<uuid:conversation_id>/typing-status/', views.get_typing_status, name='get_typing_status'),
    path('<uuid:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('<uuid:conversation_id>/send-message/', views.send_message_ajax, name='send_message_ajax'),
    path('<uuid:conversation_id>/messages/', views.get_messages_ajax, name='get_messages_ajax'),
    path('<uuid:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('<uuid:conversation_id>/clear/', views.clear_conversation, name='clear_conversation'),
    path('<uuid:conversation_id>/export/', views.export_conversation, name='export_conversation'),
    path('<uuid:conversation_id>/info/', views.conversation_info, name='conversation_info'),
    path('<uuid:conversation_id>/video/', views.video_chat, name='video_chat'),
    path('<uuid:conversation_id>/audio/', views.audio_chat, name='audio_chat'),
    path('<uuid:conversation_id>/restore/', views.restore_conversation, name='restore_conversation'),
    path('<uuid:conversation_id>/typing-ws/', views.typing_status_ws, name='typing_status_ws'),
    path('<uuid:conversation_id>/bulk-delete/', views.bulk_delete_messages, name='bulk_delete_messages'),
    path('<uuid:conversation_id>/voice/upload/', views.upload_voice_message, name='upload_conversation_voice'),

    # ===== THIS MUST BE LAST =====
    path('<uuid:conversation_id>/', views.conversation, name='conversation'),
]

# Print all URLs for verification
print("\n✅ CHAT URLS REGISTERED:")
for url in urlpatterns:
    print(f"  - {url.pattern}")
print("=" * 60 + "\n")