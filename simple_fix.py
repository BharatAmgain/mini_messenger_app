# simple_fix.py
import os
import sys
import shutil
import django

print("🎯 SIMPLE FIX FOR PUBLIC REGISTRATION")
print("=" * 50)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Clean up database and migrations
print("\n1. Cleaning up...")

# Delete database if exists
if os.path.exists("db.sqlite3"):
    os.remove("db.sqlite3")
    print("   ✅ Database deleted")

# Delete all migration files
migrations_dir = "accounts/migrations"
if os.path.exists(migrations_dir):
    for file in os.listdir(migrations_dir):
        if file != "__init__.py" and file.endswith(".py"):
            os.remove(os.path.join(migrations_dir, file))
    print("   ✅ Migration files deleted")

# Delete pycache
pycache = os.path.join(migrations_dir, "__pycache__")
if os.path.exists(pycache):
    shutil.rmtree(pycache)
    print("   ✅ Pycache cleaned")

# 2. Create fresh migrations
print("\n2. Creating fresh migrations...")
os.system("python manage.py makemigrations")

# 3. Create migration 0002 for social URLs
print("\n3. Creating social URLs migration...")
migration2_content = """from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='customuser',
            name='facebook_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='twitter_url',
            field=models.URLField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='instagram_url',
            field=models.URLField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='linkedin_url',
            field=models.URLField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='google_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
"""

with open("accounts/migrations/0002_add_social_urls.py", "w") as f:
    f.write(migration2_content)
print("   ✅ Created migration 0002")

# 4. Create migration 0003 for is_online
print("\n4. Creating is_online migration...")
migration3_content = """from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_add_social_urls'),
    ]
    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_online',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='show_online_status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='allow_message_requests',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='show_last_seen',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='show_profile_picture',
            field=models.BooleanField(default=True),
        ),
    ]
"""

with open("accounts/migrations/0003_add_is_online.py", "w") as f:
    f.write(migration3_content)
print("   ✅ Created migration 0003")

# 5. Apply migrations
print("\n5. Applying migrations...")
os.system("python manage.py migrate")

# 6. Create users
print("\n6. Creating users...")

# Initialize Django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import CustomUser
import uuid

User = get_user_model()

# Create admin user
try:
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print("   ✅ Admin user: admin / admin123")
except:
    print("   ✅ Admin user already exists")

# Create test user
try:
    test_username = f"test_{uuid.uuid4().hex[:6]}"
    test_user = CustomUser.objects.create_user(
        username=test_username,
        email=f'{test_username}@example.com',
        password='TestPass123!',
        is_active=True,
        is_online=True,
        facebook_url='https://facebook.com/test',
        show_online_status=True
    )
    print(f"   ✅ Test user: {test_username}@example.com / TestPass123!")
    print(f"   ✅ is_online: {test_user.is_online}")
    print(f"   ✅ facebook_url: {test_user.facebook_url}")
except Exception as e:
    print(f"   ⚠️  Error creating test user: {e}")

print("\n" + "=" * 50)
print("✅ FIX COMPLETE!")
print("=" * 50)
print("\n👉 Start server: python manage.py runserver")
print("👉 Register at: http://127.0.0.1:8000/accounts/register/")
print("👉 Login at: http://127.0.0.1:8000/accounts/login/")
print("\n👉 Production URL after push:")
print("   https://connect-io-0cql.onrender.com/accounts/register/")
print("=" * 50)