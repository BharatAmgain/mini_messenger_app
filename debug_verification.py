# debug_verification.py
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from accounts.models import CustomUser, OTPVerification
from django.utils import timezone
from django.contrib.auth import authenticate


def debug_user_verification():
    print("🔍 DEBUG: User Verification Status")
    print("=" * 50)

    # Check all users
    users = CustomUser.objects.all()
    for user in users:
        print(f"User: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Phone: {user.phone_number}")
        print(f"  is_verified: {user.is_verified}")
        print(f"  Last login: {user.last_login}")

        # Check OTP verifications for this user
        otps = OTPVerification.objects.filter(user=user, verification_type='account_verification')
        print(f"  Total OTP verifications: {otps.count()}")

        for otp in otps:
            print(f"    OTP ID: {otp.id}")
            print(f"    OTP Code: {otp.otp_code}")
            print(f"    is_verified: {otp.is_verified}")
            print(f"    Created: {otp.created_at}")
            print(f"    Verified at: {otp.verified_at}")
            print(f"    Expired: {otp.is_expired()}")
        print("-" * 30)


def fix_user_verification(username):
    """Manually fix a user's verification status"""
    try:
        user = CustomUser.objects.get(username=username)
        print(f"\n🔧 Fixing verification for user: {username}")
        print(f"Current is_verified: {user.is_verified}")

        # Check if user has any verified OTP
        verified_otp = OTPVerification.objects.filter(
            user=user,
            verification_type='account_verification',
            is_verified=True
        ).exists()

        if verified_otp:
            print("✅ User has verified OTP - updating is_verified to True")
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            print(f"✅ Updated is_verified to: {user.is_verified}")
        else:
            print("❌ No verified OTP found for this user")
            print("Creating a test OTP verification...")

            # Create a test OTP verification
            otp = OTPVerification.objects.create(
                user=user,
                verification_type='account_verification',
                otp_code='123456',
                email=user.email,
                phone_number=user.phone_number,
                is_verified=True,
                verified_at=timezone.now(),
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )
            print(f"✅ Created test OTP: {otp.id}")

            # Now update user
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            print(f"✅ Updated is_verified to: {user.is_verified}")

    except CustomUser.DoesNotExist:
        print(f"❌ User {username} not found")


if __name__ == "__main__":
    print("1. Checking all users...")
    debug_user_verification()

    # Fix specific user (change 'bharat' to your username)
    fix_user_verification('bharat')

    print("\n✅ Debug complete!")