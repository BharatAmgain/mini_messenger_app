# find_admin.py - Find admin/superuser accounts
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from accounts.models import CustomUser

print("🔍 Searching for Admin/Superuser Accounts...")
print("=" * 60)

# Find all superusers
superusers = CustomUser.objects.filter(is_superuser=True)
staff_users = CustomUser.objects.filter(is_staff=True)

print("👑 SUPERUSERS (Full Admin Access):")
print("-" * 40)
if superusers.exists():
    for user in superusers:
        print(f"  Username: {user.username}")
        print(f"  Email:    {user.email}")
        print(f"  Phone:    {user.phone_number}")
        print(f"  Last Login: {user.last_login}")
        print(f"  Active:   {user.is_active}")
        print(f"  Verified: {user.is_verified}")
        print("-" * 30)
else:
    print("  ❌ No superusers found!")

print("\n👔 STAFF USERS (Partial Admin Access):")
print("-" * 40)
if staff_users.exists():
    for user in staff_users:
        print(f"  Username: {user.username}")
        print(f"  Email:    {user.email}")
        print(f"  Superuser: {user.is_superuser}")
        print(f"  Last Login: {user.last_login}")
        print("-" * 30)
else:
    print("  ❌ No staff users found!")

print("\n📋 ALL USERS:")
print("-" * 40)
all_users = CustomUser.objects.all()
for i, user in enumerate(all_users, 1):
    print(f"{i:2}. {user.username:15} | {user.email:30} | Superuser: {user.is_superuser} | Staff: {user.is_staff}")