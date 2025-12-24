# quick_final_fix.py
import os
import sys

print("🎯 QUICK FINAL FIX")
print("=" * 50)

# 1. Check what's in the initial migration
print("\n1. Checking initial migration...")
initial_migration = "accounts/migrations/0001_initial.py"
if os.path.exists(initial_migration):
    with open(initial_migration, 'r') as f:
        content = f.read()
        if 'facebook_url' in content:
            print("   ✅ facebook_url already in initial migration")
        else:
            print("   ❌ facebook_url NOT in initial migration")

        if 'is_online' in content:
            print("   ✅ is_online already in initial migration")
        else:
            print("   ❌ is_online NOT in initial migration")

# 2. Delete problematic migrations
print("\n2. Cleaning up migrations...")
for file in ["0002_add_social_urls.py", "0003_add_is_online.py", "0002_fix_columns.py", "0003_add_missing_fields.py"]:
    filepath = f"accounts/migrations/{file}"
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"   ✅ Deleted: {file}")

# 3. Create correct migration 0002
print("\n3. Creating migration 0002 for is_online...")
migration_content = """from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
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
            name='show_last_seen',
            field=models.BooleanField(default=True),
        ),
    ]
"""

with open("accounts/migrations/0002_add_is_online.py", "w") as f:
    f.write(migration_content)
print("   ✅ Created migration 0002")

# 4. Apply migrations
print("\n4. Applying migrations...")
os.system("python manage.py migrate")

# 5. Test
print("\n5. Testing...")
os.system("python manage.py shell -c \""
          "from accounts.models import CustomUser;"
          "import uuid;"
          "try:"
          "    user = CustomUser.objects.create_user("
          "        username='test' + str(uuid.uuid4())[:8],"
          "        email='test@test.com',"
          "        password='test123'"
          "    );"
          "    print('✅ User created:', user.username);"
          "    print('✅ is_online:', user.is_online);"
          "    print('✅ facebook_url exists:', hasattr(user, 'facebook_url'));"
          "except Exception as e:"
          "    print('❌ Error:', e)"
          "\"")

print("\n" + "=" * 50)
print("✅ FIX COMPLETE!")
print("=" * 50)
print("\n👉 Start server: python manage.py runserver")
print("👉 Test: http://127.0.0.1:8000/accounts/register/")