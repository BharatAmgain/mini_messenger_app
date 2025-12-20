# accounts/urls.py - COMPLETE VERSION
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    register, login_view, logout_view, profile, profile_edit,
    settings_main, privacy_settings, update_privacy_settings,
    notifications, mark_notification_read, mark_notification_unread,
    mark_all_notifications_read, mark_all_notifications_unread,
    archive_notification, archive_all_notifications, delete_notification,
    clear_all_notifications, notification_settings, update_notification_preferences,
    get_unread_count, update_notification_settings, deactivate_account,
    delete_account, clear_chat_history, export_data, update_theme,
    toggle_two_factor, send_friend_request, cancel_friend_request,
    accept_friend_request, reject_friend_request, friend_requests,
    remove_friend, password_reset_request, password_reset_verify_otp,
    password_reset_confirm, password_change_with_otp, verify_password_change_otp,
    resend_otp, send_verification_otp, verify_account_otp,
    update_profile, get_profile, debug_verification_status,
    force_verify_user, debug_session, test_profile_update, refresh_profile,
    debug_google_oauth, test_google_login
)

urlpatterns = [
    # ========== AUTHENTICATION URLS ==========
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # ========== SOCIAL AUTH URLS ==========
    path('login/google-oauth2/', views.login_view, name='google_login'),
    path('login/facebook/', views.login_view, name='facebook_login'),

    # ========== PROFILE URLS ==========
    path('profile/', profile, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/update/', update_profile, name='update_profile'),
    path('profile/get/', get_profile, name='get_profile'),

    # ========== SETTINGS URLS ==========
    path('settings/', settings_main, name='settings_main'),
    path('settings/privacy/', privacy_settings, name='privacy_settings'),
    path('settings/privacy/update/', update_privacy_settings, name='update_privacy_settings'),
    path('settings/notifications/', notification_settings, name='notification_settings'),
    path('settings/notifications/update/', update_notification_preferences, name='update_notification_preferences'),
    path('settings/update/', update_notification_settings, name='update_notification_settings'),
    path('settings/deactivate/', deactivate_account, name='deactivate_account'),
    path('settings/delete/', delete_account, name='delete_account'),
    path('settings/clear-chat/', clear_chat_history, name='clear_chat_history'),
    path('settings/export-data/', export_data, name='export_data'),
    path('settings/update-theme/', update_theme, name='update_theme'),
    path('settings/toggle-two-factor/', toggle_two_factor, name='toggle_two_factor'),

    # ========== NOTIFICATION URLS ==========
    path('notifications/', notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-unread/<int:notification_id>/', mark_notification_unread, name='mark_notification_unread'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/mark-all-unread/', mark_all_notifications_unread, name='mark_all_notifications_unread'),
    path('notifications/archive/<int:notification_id>/', archive_notification, name='archive_notification'),
    path('notifications/archive-all/', archive_all_notifications, name='archive_all_notifications'),
    path('notifications/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
    path('notifications/clear-all/', clear_all_notifications, name='clear_all_notifications'),
    path('notifications/unread-count/', get_unread_count, name='get_unread_count'),

    # ========== FRIEND & SOCIAL URLS ==========
    path('friend-requests/', friend_requests, name='friend_requests'),
    path('friend-request/send/<int:user_id>/', send_friend_request, name='send_friend_request'),
    path('friend-request/cancel/<int:user_id>/', cancel_friend_request, name='cancel_friend_request'),
    path('friend-request/accept/<int:request_id>/', accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', reject_friend_request, name='reject_friend_request'),
    path('friend/remove/<int:user_id>/', remove_friend, name='remove_friend'),

    # ========== PASSWORD RESET URLS ==========
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('password-change/otp/', password_change_with_otp, name='password_change_with_otp'),
    path('password-change/verify-otp/', verify_password_change_otp, name='verify_password_change_otp'),

    # ========== OTP & VERIFICATION URLS ==========
    path('resend-otp/<str:otp_type>/', resend_otp, name='resend_otp'),
    path('verification/send-otp/', send_verification_otp, name='send_verification_otp'),
    path('verification/verify-otp/', verify_account_otp, name='verify_account_otp'),

    # ========== DEBUG & TESTING URLS ==========
    path('debug/verification-status/', debug_verification_status, name='debug_verification_status'),
    path('debug/force-verify/', force_verify_user, name='force_verify_user'),
    path('debug/session/', debug_session, name='debug_session'),
    path('debug/test-profile-update/', test_profile_update, name='test_profile_update'),
    path('debug/refresh-profile/', refresh_profile, name='refresh_profile'),

    # ========== GOOGLE OAUTH DEBUG URLS ==========
    path('debug-google-oauth/', debug_google_oauth, name='debug_google_oauth'),
    path('test-google-login/', test_google_login, name='test_google_login'),

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

    # ========== PROFILE VIEW URLS (for viewing other profiles) ==========
    path('profile/<int:user_id>/', views.view_user_profile, name='view_user_profile'),

    # ========== DISCOVER & SEARCH URLS ==========
    path('discover/', views.discover_users, name='discover_users'),
    path('search/', views.search_users, name='search_users'),

    # ========== API ENDPOINTS ==========
    path('api/update-profile/', update_profile, name='api_update_profile'),
    path('api/get-profile/', get_profile, name='api_get_profile'),
    path('api/notifications/unread-count/', get_unread_count, name='api_unread_count'),
]

# Add a catch-all for social auth if needed
try:
    from social_django.urls import urlpatterns as social_urls

    urlpatterns += social_urls
except ImportError:
    pass