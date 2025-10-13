from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import PasswordResetToken, TwoFactorAuth, PhoneVerification
from .forms import CustomPasswordResetForm, CustomSetPasswordForm, TwoFactorSetupForm, VerifyOTPForm

User = get_user_model()


def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                # Generate token
                token = default_token_generator.make_token(user)
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=timezone.now() + timedelta(hours=1)
                )

                # Send email
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = f"{request.scheme}://{request.get_host()}/auth/password-reset-confirm/{uid}/{token}/"

                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                return redirect('password_reset_done')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'authentication/password_reset.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')
        else:
            form = CustomSetPasswordForm(user)

        return render(request, 'authentication/password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'authentication/password_reset_invalid.html')


@login_required
def setup_two_factor(request):
    two_fa, created = TwoFactorAuth.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            two_fa.method = form.cleaned_data['method']
            two_fa.phone_number = form.cleaned_data.get('phone_number')
            two_fa.generate_secret_key()  # Generate secret key
            two_fa.save()

            # Generate and send OTP
            otp = two_fa.generate_otp()

            if two_fa.method == 'email':
                send_mail(
                    'Your Verification Code',
                    f'Your verification code is: {otp}',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=False,
                )
            elif two_fa.method == 'phone':
                # Store phone verification
                PhoneVerification.objects.create(
                    phone_number=two_fa.phone_number,
                    code=otp
                )

            return redirect('verify_two_factor_setup')
    else:
        form = TwoFactorSetupForm(initial={
            'method': two_fa.method,
            'phone_number': two_fa.phone_number
        })

    return render(request, 'authentication/setup_two_factor.html', {'form': form})


@login_required
def verify_two_factor_setup(request):
    two_fa = TwoFactorAuth.objects.get(user=request.user)

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            if two_fa.verify_otp(form.cleaned_data['otp']):
                two_fa.is_enabled = True
                two_fa.save()
                return redirect('two_factor_success')
            else:
                form.add_error('otp', 'Invalid verification code')
    else:
        form = VerifyOTPForm()

    return render(request, 'authentication/verify_two_factor.html', {
        'form': form,
        'method': two_fa.method
    })


@login_required
def two_factor_success(request):
    return render(request, 'authentication/two_factor_success.html')


def password_reset_complete(request):
    return render(request, 'authentication/password_reset_complete.html')