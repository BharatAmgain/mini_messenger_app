# messenger_app/accounts/urls.py - COMPLETE FIXED VERSION
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Social Auth URLs
    path('social-auth/', include('social_django.urls', namespace='social')),

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Settings URLs
    path('settings/', views.settings_main, name='settings_main'),
    path('privacy-settings/', views.privacy_settings, name='privacy_settings'),
    path('update-privacy-settings/', views.update_privacy_settings, name='update_privacy_settings'),
    path('update-notification-settings/', views.update_notification_settings, name='update_notification_settings'),

    # New Settings URLs
    path('deactivate-account/', views.deactivate_account, name='deactivate_account'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('clear-chat-history/', views.clear_chat_history, name='clear_chat_history'),
    path('export-data/', views.export_data, name='export_data'),
    path('update-theme/', views.update_theme, name='update_theme'),
    path('toggle-two-factor/', views.toggle_two_factor, name='toggle_two_factor'),

    # Enhanced Notification URLs - ALL NOTIFICATION URLS GO HERE
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

    # Notification Settings
    path('notification-settings/', views.notification_settings, name='notification_settings'),
    path('update-notification-preferences/', views.update_notification_preferences,
         name='update_notification_preferences'),

    # Unread Count URL
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),

    # Friend Request URLs - ADD THESE
    path('friend-requests/', views.friend_requests, name='friend_requests'),
    path('send-friend-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('cancel-friend-request/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),

    # Password Change URLs (Django built-in - kept for backup)
    path('password-change-old/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password-change/done/'
    ), name='password_change_old'),

    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    # Password Reset URLs (Django built-in - kept for backup)
    path('password-reset-old/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ),
         name='password_reset_old'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # ========== OTP-BASED AUTHENTICATION URLS ==========

    # OTP-based password reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify-otp/', views.password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),

    # OTP-based password change
    path('password-change/', views.password_change_with_otp, name='password_change_with_otp'),
    path('password-change/verify-otp/', views.verify_password_change_otp, name='verify_password_change_otp'),

    # Account verification with OTP
    path('send-verification-otp/', views.send_verification_otp, name='send_verification_otp'),
    path('verify-account-otp/', views.verify_account_otp, name='verify_account_otp'),

    # Resend OTP
    path('resend-otp/<str:otp_type>/', views.resend_otp, name='resend_otp'),

    # API URLs for profile updates
    path('api/profile/update/', views.update_profile, name='update_profile_api'),
    path('api/profile/get/', views.get_profile, name='get_profile_api'),
]