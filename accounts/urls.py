# accounts/urls.py - FIXED VERSION
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ========== AUTHENTICATION URLS ==========
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ========== SOCIAL AUTH URLS ==========
    path('login/google-oauth2/', views.login_view, name='google_login'),
    path('login/facebook/', views.login_view, name='facebook_login'),

    # ========== PROFILE URLS ==========
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/get/', views.get_profile, name='get_profile'),
    path('profile/<int:user_id>/', views.view_user_profile, name='view_user_profile'),

    # ========== SETTINGS URLS ==========
    path('settings/', views.settings_main, name='settings_main'),
    path('settings/privacy/', views.privacy_settings, name='privacy_settings'),
    path('settings/privacy/update/', views.update_privacy_settings, name='update_privacy_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/notifications/update/', views.update_notification_preferences,
         name='update_notification_preferences'),
    path('settings/update/', views.update_notification_settings, name='update_notification_settings'),
    path('settings/deactivate/', views.deactivate_account, name='deactivate_account'),
    path('settings/delete/', views.delete_account, name='delete_account'),
    path('settings/clear-chat/', views.clear_chat_history, name='clear_chat_history'),
    path('settings/export-data/', views.export_data, name='export_data'),
    path('settings/update-theme/', views.update_theme, name='update_theme'),
    path('settings/toggle-two-factor/', views.toggle_two_factor, name='toggle_two_factor'),

    # ========== NOTIFICATION URLS ==========
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-unread/<int:notification_id>/', views.mark_notification_unread,
         name='mark_notification_unread'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/mark-all-unread/', views.mark_all_notifications_unread, name='mark_all_notifications_unread'),
    path('notifications/archive/<int:notification_id>/', views.archive_notification, name='archive_notification'),
    path('notifications/archive-all/', views.archive_all_notifications, name='archive_all_notifications'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('notifications/unread-count/', views.get_unread_count, name='get_unread_count'),

    # ========== FRIEND & SOCIAL URLS ==========
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('friend-request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/cancel/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friend-request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('discover/', views.discover_users, name='discover_users'),
    path('search/', views.search_users, name='search_users'),

    # ========== PASSWORD RESET URLS ==========
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-change/otp/', views.password_change_with_otp, name='password_change_with_otp'),
    path('password-change/verify-otp/', views.verify_password_change_otp, name='verify_password_change_otp'),

    # ========== OTP & VERIFICATION URLS ==========
    path('resend-otp/<str:otp_type>/', views.resend_otp, name='resend_otp'),
    path('verification/send-otp/', views.send_verification_otp, name='send_verification_otp'),
    path('verification/verify-otp/', views.verify_account_otp, name='verify_account_otp'),

    # ========== DEBUG & TESTING URLS ==========
    path('debug/verification-status/', views.debug_verification_status, name='debug_verification_status'),
    path('debug/force-verify/', views.force_verify_user, name='force_verify_user'),
    path('debug/session/', views.debug_session, name='debug_session'),
    path('debug/test-profile-update/', views.test_profile_update, name='test_profile_update'),
    path('debug/refresh-profile/', views.refresh_profile, name='refresh_profile'),

    # ========== GOOGLE OAUTH DEBUG URLS ==========
    path('debug-google-oauth/', views.debug_google_oauth, name='debug_google_oauth'),
    path('test-google-login/', views.test_google_login, name='test_google_login'),

    # ========== DJANGO AUTH DEFAULT URLS (for fallback) ==========
    path('password-reset/django/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), name='password_reset_complete'),

    # ========== API ENDPOINTS ==========
    path('api/update-profile/', views.update_profile, name='api_update_profile'),
    path('api/get-profile/', views.get_profile, name='api_get_profile'),
    path('api/notifications/unread-count/', views.get_unread_count, name='api_unread_count'),
]

# Add a catch-all for social auth if needed
try:
    from social_django.urls import urlpatterns as social_urls

    urlpatterns += social_urls
except ImportError:
    pass