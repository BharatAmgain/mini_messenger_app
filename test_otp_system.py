# test_otp_system.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()

    from accounts.models import CustomUser, PasswordResetOTP
    from django.contrib.auth.hashers import make_password

    print("=" * 60)
    print("OTP SYSTEM TEST")
    print("=" * 60)

    # Create or get test user
    email = "test@example.com"
    phone = "+9779866399895"  # Your phone number

    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': 'testuser',
            'password': make_password('test123'),
            'is_active': True,
            'phone_number': phone
        }
    )

    print(f"User: {user.email} | Phone: {user.phone_number}")
    print(f"User created: {created}")

    # Test OTP creation
    print("\n1. Testing Email OTP:")
    otp_email = PasswordResetOTP.create_password_reset_otp(
        user=user,
        email=user.email
    )
    print(f"OTP Code: {otp_email.otp_code}")
    print(f"Expires: {otp_email.expires_at}")

    # Test OTP verification
    print("\n2. Testing OTP Verification:")
    success, message = otp_email.verify_and_use(otp_email.otp_code)
    print(f"Success: {success} | Message: {message}")

    # Test invalid OTP
    print("\n3. Testing Invalid OTP:")
    success, message = otp_email.verify_and_use("000000")
    print(f"Success: {success} | Message: {message}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()