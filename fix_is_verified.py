# create fix_is_verified.py in your project root
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from accounts.models import CustomUser


def fix_is_verified():
    """Fix is_verified field for all users"""
    users = CustomUser.objects.all()
    for user in users:
        # Check if is_verified is a function/partial
        if callable(user.is_verified):
            print(f"Fixing user {user.username}: is_verified is callable")
            # Set to False by default
            user.is_verified = False
            user.save(update_fields=['is_verified'])
        elif user.is_verified not in [True, False]:
            print(f"Fixing user {user.username}: is_verified = {user.is_verified}")
            user.is_verified = False
            user.save(update_fields=['is_verified'])

    print(f"Fixed {users.count()} users")


if __name__ == '__main__':
    fix_is_verified()