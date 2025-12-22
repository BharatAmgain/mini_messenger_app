# messenger/otp_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
import pyotp
import qrcode
import io
import base64
from django.http import HttpResponse
from django.conf import settings


@login_required
def setup_otp(request):
    """Setup Two-Factor Authentication for user"""
    user = request.user

    # Check if user already has OTP device
    existing_devices = devices_for_user(user)
    if existing_devices:
        messages.info(request, 'Two-factor authentication is already setup.')
        return redirect('otp_status')

    # Generate secret key
    secret = pyotp.random_base32()

    # Create TOTP device
    device = TOTPDevice.objects.create(
        user=user,
        name='default',
        confirmed=False,
        key=secret
    )

    # Generate provisioning URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=settings.SITE_NAME
    )

    # Generate QR code
    qr = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'secret': secret,
        'provisioning_uri': provisioning_uri,
        'qr_code': qr_code,
    }

    return render(request, 'otp/setup.html', context)


@login_required
def verify_otp_setup(request):
    """Verify OTP setup with code"""
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()

        if not otp_code:
            messages.error(request, 'Please enter OTP code.')
            return redirect('verify_otp_setup')

        # Get user's unconfirmed device
        devices = TOTPDevice.objects.filter(user=request.user, confirmed=False)
        if not devices.exists():
            messages.error(request, 'No pending OTP setup found.')
            return redirect('setup_otp')

        device = devices.first()

        # Verify OTP
        if device.verify_token(otp_code):
            device.confirmed = True
            device.save()

            # Enable 2FA for user
            from accounts.models import CustomUser
            user = CustomUser.objects.get(id=request.user.id)
            user.two_factor_enabled = True
            user.save()

            messages.success(request, 'Two-factor authentication setup successfully!')
            return redirect('otp_status')
        else:
            messages.error(request, 'Invalid OTP code. Please try again.')

    return render(request, 'otp/verify_setup.html')


@login_required
def otp_status(request):
    """Show OTP status"""
    user = request.user
    devices = devices_for_user(user)
    has_otp = bool(devices)

    context = {
        'has_otp': has_otp,
        'devices': devices,
        'two_factor_enabled': user.two_factor_enabled,
    }

    return render(request, 'otp/status.html', context)


@login_required
def disable_otp(request):
    """Disable Two-Factor Authentication"""
    if request.method == 'POST':
        # Delete all OTP devices for user
        TOTPDevice.objects.filter(user=request.user).delete()

        # Disable 2FA for user
        from accounts.models import CustomUser
        user = CustomUser.objects.get(id=request.user.id)
        user.two_factor_enabled = False
        user.save()

        messages.success(request, 'Two-factor authentication has been disabled.')

    return redirect('otp_status')


def verify_login_otp(request):
    """Verify OTP during login"""
    # This would be called during the login process
    # You need to store user_id in session during login
    user_id = request.session.get('otp_user_id')

    if not user_id:
        messages.error(request, 'Invalid OTP verification request.')
        return redirect('accounts:login')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()

        if not otp_code:
            messages.error(request, 'Please enter OTP code.')
            return render(request, 'otp/verify_login.html')

        # Get user and verify OTP
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
            devices = devices_for_user(user)

            for device in devices:
                if device.verify_token(otp_code):
                    # Clear session
                    if 'otp_user_id' in request.session:
                        del request.session['otp_user_id']

                    # Login user
                    from django.contrib.auth import login
                    login(request, user)

                    messages.success(request, 'Login successful!')
                    return redirect('chat:chat_home')

            messages.error(request, 'Invalid OTP code.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')

    return render(request, 'otp/verify_login.html')