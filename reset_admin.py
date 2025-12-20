# reset_admin.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from accounts.models import CustomUser

print("🔄 COMPLETE ADMIN RESET")
print("=" * 60)

# 1. List current admins
print("\n📋 CURRENT ADMINS:")
current_admins = CustomUser.objects.filter(is_superuser=True) | CustomUser.objects.filter(is_staff=True)
if current_admins.exists():
    for admin in current_admins:
        print(f"  • {admin.username} ({admin.email}) - Superuser: {admin.is_superuser}, Staff: {admin.is_staff}")
else:
    print("  No admin users found")

# 2. Remove all admin privileges
print("\n🗑️ REMOVING ADMIN PRIVILEGES...")
count = 0
for user in CustomUser.objects.all():
    if user.is_superuser or user.is_staff:
        user.is_superuser = False
        user.is_staff = False
        user.save()
        count += 1
        print(f"  Removed admin from: {user.username}")

print(f"✅ Removed admin privileges from {count} users")

# 3. Create fresh admins
print("\n👑 CREATING NEW ADMINS...")
print("-" * 40)

# Delete existing admin users if they exist
CustomUser.objects.filter(username='admin').delete()
CustomUser.objects.filter(username='newadmin').delete()
CustomUser.objects.filter(username='bharat').delete()

# Admin 1: System Admin
admin1 = CustomUser.objects.create_superuser(
    username='admin',
    email='admin@connect.io',
    password='Admin@2024',
    first_name='System',
    last_name='Administrator',
    phone_number='+12345678901',
    is_verified=True
)
print(f"✅ Admin 1: {admin1.username} / Admin@2024")

# Admin 2: Your Personal Admin
admin2 = CustomUser.objects.create_superuser(
    username='bharat',
    email='amgaibharat46@gmail.com',
    password='Bharat@2024',
    first_name='Bharat',
    last_name='Amgain',
    phone_number='+9779866399895',
    is_verified=True
)
print(f"✅ Admin 2: {admin2.username} / Bharat@2024")

# Admin 3: Backup Admin
admin3 = CustomUser.objects.create_superuser(
    username='superuser',
    email='superuser@connect.io',
    password='Super@2024',
    first_name='Backup',
    last_name='Admin',
    phone_number='+19876543210',
    is_verified=True
)
print(f"✅ Admin 3: {admin3.username} / Super@2024")

# 4. Verify creation
print("\n🔍 VERIFYING NEW ADMINS:")
print("-" * 40)
new_admins = CustomUser.objects.filter(is_superuser=True)
for admin in new_admins:
    print(f"  • {admin.username} - {admin.email}")

print("\n" + "=" * 60)
print("🎉 ADMIN RESET COMPLETE!")
print("=" * 60)

print("\n🔑 YOUR NEW ADMIN CREDENTIALS:")
print("╔══════════════════════════════════════════════════════════╗")
print("║ 1. SYSTEM ADMIN:                                         ║")
print("║    Username: admin                                       ║")
print("║    Password: Admin@2024                                  ║")
print("║    Email: admin@connect.io                               ║")
print("║                                                          ║")
print("║ 2. YOUR PERSONAL ADMIN:                                  ║")
print("║    Username: bharat                                      ║")
print("║    Password: Bharat@2024                                 ║")
print("║    Email: amgaibharat46@gmail.com                        ║")
print("║                                                          ║")
print("║ 3. BACKUP ADMIN:                                         ║")
print("║    Username: superuser                                   ║")
print("║    Password: Super@2024                                  ║")
print("║    Email: superuser@connect.io                           ║")
print("╚══════════════════════════════════════════════════════════╝")

print("\n🌐 Login URLs:")
print("• Local:      http://localhost:8000/admin/")
print("• Production: https://connect-io-0cql.onrender.com/admin/")

print("\n⚡ Quick test:")
print("python manage.py runserver")
print("Then go to: http://localhost:8000/admin/")