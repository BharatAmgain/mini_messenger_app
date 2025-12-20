# fix_verification.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from accounts.models import CustomUser


def fix_user_verification():
    # Find your user
    username = 'bharat'  # Change to your username if different

    try:
        user = CustomUser.objects.get(username=username)
        print(f"Found user: {user.username}")
        print(f"Current is_verified: {user.is_verified}")

        # Manually set to verified
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        print(f"✅ Updated {user.username} to verified!")
        print(f"New is_verified: {user.is_verified}")

        # Also check the profile
        print(f"\nProfile data:")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Phone: {user.phone_number}")
        print(f"  Verified: {user.is_verified}")

    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found!")
        print("\nAvailable users:")
        for u in CustomUser.objects.all():
            print(f"  - {u.username} (email: {u.email}, verified: {u.is_verified})")


if __name__ == "__main__":
    fix_user_verification()