# messenger_app/accounts/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/get/', views.get_profile, name='get_profile'),
    path('profile/refresh/', views.refresh_profile, name='refresh_profile'),

    # Settings URLs
    path('settings/', views.settings_main, name='settings_main'),
    path('settings/privacy/', views.privacy_settings, name='privacy_settings'),
    path('settings/privacy/update/', views.update_privacy_settings, name='update_privacy_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/notifications/update/', views.update_notification_preferences,
         name='update_notification_preferences'),
    path('settings/theme/update/', views.update_theme, name='update_theme'),
    path('settings/two-factor/toggle/', views.toggle_two_factor, name='toggle_two_factor'),

    # Account Management URLs
    path('settings/deactivate/', views.deactivate_account, name='deactivate_account'),
    path('settings/delete/', views.delete_account, name='delete_account'),
    path('settings/clear-chat-history/', views.clear_chat_history, name='clear_chat_history'),
    path('settings/export-data/', views.export_data, name='export_data'),

    # Password Management URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-change/', views.password_change_with_otp, name='password_change_with_otp'),
    path('password-change/verify-otp/', views.verify_password_change_otp, name='verify_password_change_otp'),
    path('resend-otp/<str:otp_type>/', views.resend_otp, name='resend_otp'),

    # OTP Verification URLs
    path('verify/send-otp/', views.send_verification_otp, name='send_verification_otp'),
    path('verify/account-otp/', views.verify_account_otp, name='verify_account_otp'),

    # Notifications URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/unread/', views.mark_notification_unread,
         name='mark_notification_unread'),
    path('notifications/<int:notification_id>/archive/', views.archive_notification, name='archive_notification'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/mark-all-unread/', views.mark_all_notifications_unread, name='mark_all_notifications_unread'),
    path('notifications/archive-all/', views.archive_all_notifications, name='archive_all_notifications'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),

    # ✅ ADD THIS MISSING URL:
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),

    # Friends URLs
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('friend-requests/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-requests/cancel/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friend-requests/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-requests/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),

    # Debug URLs (Remove in production)
    path('debug/verification-status/', views.debug_verification_status, name='debug_verification_status'),
    path('debug/force-verify/', views.force_verify_user, name='force_verify_user'),
    path('debug/session/', views.debug_session, name='debug_session'),
    path('debug/test-profile-update/', views.test_profile_update, name='test_profile_update'),
]