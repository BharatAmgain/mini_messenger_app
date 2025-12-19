# check_database_safe.py - SAFE TO COMMIT
import os
import django
from decouple import config

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

print("=== SAFE Database Check ===")

# Get credentials from environment (safe)
TEST_EMAIL = config('TEST_EMAIL', default='test@example.com')
TEST_PASSWORD = config('TEST_PASSWORD', default='TestPass123!')
TEST_PHONE = config('TEST_PHONE', default='+9779800000000')

# Check connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Database connection: WORKING")
except Exception as e:
    print(f"❌ Database connection FAILED: {e}")

# Check tables
try:
    User = get_user_model()
    count = User.objects.count()
    print(f"📊 Total users: {count}")

    # List existing users (email only for privacy)
    if count > 0:
        print("👥 Existing users:")
        for user in User.objects.all()[:5]:  # Show first 5 only
            print(f"   - {user.email} (Verified: {user.is_verified})")

    # Create test user if none exist
    if count == 0:
        print("\n⚠️  No users found. Creating test user...")
        user = User.objects.create_user(
            username='testuser',
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            phone_number=TEST_PHONE,
            is_verified=True
        )
        print(f"✅ Created test user: {TEST_EMAIL}")
        print(f"   Password: [HIDDEN - from environment]")
        print(f"   Phone: {TEST_PHONE}")

except Exception as e:
    print(f"❌ User table error: {e}")