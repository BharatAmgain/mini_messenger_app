# messenger_app/accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

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

    # Notification URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),

    # Password Change URLs
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change.html',
             success_url='/accounts/password-change/done/'
         ),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ),
         name='password_change_done'),

    # Password Reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ),
         name='password_reset'),
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
]