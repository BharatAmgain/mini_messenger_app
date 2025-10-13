from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='authentication/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),
    path('setup-two-factor/', views.setup_two_factor, name='setup_two_factor'),
    path('verify-two-factor/', views.verify_two_factor_setup, name='verify_two_factor_setup'),
    path('two-factor-success/', views.two_factor_success, name='two_factor_success'),
]