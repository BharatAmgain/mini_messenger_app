# accounts/urls.py - COMPLETE FIXED VERSION
from django.urls import path
from . import views

app_name = 'accounts'  # KEEP THIS - accounts app uses namespace

urlpatterns = [
    # Root URL redirects to login or chat_home based on authentication
    path('', views.root_redirect, name='root_redirect'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/get/', views.get_profile, name='get_profile'),

    # Settings
    path('settings/', views.settings_main, name='settings_main'),
    path('settings/privacy/', views.privacy_settings, name='privacy_settings'),
    path('settings/privacy/update/', views.update_privacy_settings, name='update_privacy_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/notifications/update/', views.update_notification_preferences,
         name='update_notification_preferences'),
    path('settings/theme/', views.update_theme, name='update_theme'),
    path('settings/two-factor/', views.toggle_two_factor, name='toggle_two_factor'),
    path('settings/deactivate/', views.deactivate_account, name='deactivate_account'),
    path('settings/delete/', views.delete_account, name='delete_account'),
    path('settings/export/', views.export_data, name='export_data'),
    path('settings/clear-chat/', views.clear_chat_history, name='clear_chat_history'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/unread/<int:notification_id>/', views.mark_notification_unread,
         name='mark_notification_unread'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/unread-all/', views.mark_all_notifications_unread, name='mark_all_notifications_unread'),
    path('notifications/archive/<int:notification_id>/', views.archive_notification, name='archive_notification'),
    path('notifications/archive-all/', views.archive_all_notifications, name='archive_all_notifications'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),

    # Friends
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('send-friend-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('cancel-friend-request/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),

    # Discover and Search
    path('discover/', views.discover_users, name='discover_users_accounts'),  # Different name to avoid conflict
    path('search/', views.search_users, name='search_users'),

    # Password Reset (with OTP)
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-change/otp/', views.password_change_with_otp, name='password_change_with_otp'),
    path('password-change/verify-otp/', views.verify_password_change_otp, name='verify_password_change_otp'),
    path('resend-otp/<str:otp_type>/', views.resend_otp, name='resend_otp'),

    # Account Verification
    path('verification/send-otp/', views.send_verification_otp, name='send_verification_otp'),
    path('verification/verify-otp/', views.verify_account_otp, name='verify_account_otp'),

    # Two-Factor Authentication (OTP)
    path('otp/setup/', views.setup_otp, name='setup_otp'),
    path('otp/verify-setup/', views.verify_otp_setup, name='verify_otp_setup'),
    path('otp/status/', views.otp_status, name='otp_status'),
    path('otp/disable/', views.disable_otp, name='disable_otp'),
    path('otp/verify-login/', views.verify_login_otp, name='verify_login_otp'),

    # Debug endpoints
    path('debug-verification/', views.debug_verification_status, name='debug_verification_status'),
    path('debug-session/', views.debug_session, name='debug_session'),
    path('force-verify/', views.force_verify_user, name='force_verify_user'),
    path('test-profile-update/', views.test_profile_update, name='test_profile_update'),
    path('refresh-profile/', views.refresh_profile, name='refresh_profile'),

    # Google OAuth debug
    path('debug-google-oauth/', views.debug_google_oauth, name='debug_google_oauth'),
    path('test-google-login/', views.test_google_login, name='test_google_login'),
]