# check_database.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

print("=== Database Check ===")

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
    print(f"✅ User table exists with {count} users")

    if count == 0:
        print("⚠️  No users found. Creating test user...")
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            phone_number='+9779800000000',
            is_verified=True
        )
        print("✅ Created test user: test@example.com")
except Exception as e:
    print(f"❌ User table error: {e}")