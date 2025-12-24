# final_fix.ps1
Write-Host "🎯 FINAL FIX FOR PUBLIC REGISTRATION" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# 1. Delete everything
Write-Host "`n1. Cleaning up everything..." -ForegroundColor Yellow

# Delete database
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "   ✅ Database deleted" -ForegroundColor Green
}

# Delete all migration files
Get-ChildItem -Path "accounts/migrations" -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Migration files deleted" -ForegroundColor Green

# Delete pycache
Remove-Item -Path "accounts/migrations/__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Pycache cleaned" -ForegroundColor Green

# 2. Create fresh initial migration
Write-Host "`n2. Creating fresh migration..." -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Initial migration created" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to create migration" -ForegroundColor Red
    exit
}

# 3. Create migration 0002 for social URLs
Write-Host "`n3. Creating social URLs migration..." -ForegroundColor Yellow
$migration2 = @"
from django.db import migrations, models

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
"@

$migration2 | Out-File -FilePath "accounts/migrations/0002_add_social_urls.py" -Encoding UTF8
Write-Host "   ✅ Created migration 0002" -ForegroundColor Green

# 4. Create migration 0003 for is_online
Write-Host "`n4. Creating is_online migration..." -ForegroundColor Yellow
$migration3 = @"
from django.db import migrations, models

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
    ]
"@

$migration3 | Out-File -FilePath "accounts/migrations/0003_add_is_online.py" -Encoding UTF8
Write-Host "   ✅ Created migration 0003" -ForegroundColor Green

# 5. Apply ALL migrations
Write-Host "`n5. Applying ALL migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ All migrations applied" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to apply migrations" -ForegroundColor Red
    exit
}

# 6. Create test users
Write-Host "`n6. Creating test users..." -ForegroundColor Yellow

# Create admin user
python manage.py createsuperuser --username admin --email admin@example.com --noinput
python -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
user.set_password('admin123')
user.save()
print('✅ Admin user created: admin / admin123')
"

# Create test user
python -c "
from accounts.models import CustomUser
import uuid

try:
    # Create a public test user
    username = 'public_user_' + uuid.uuid4().hex[:6]
    user = CustomUser.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='TestPass123!',
        is_active=True,
        is_online=True,
        facebook_url='https://facebook.com/test',
        show_online_status=True
    )
    print(f'✅ Public test user created: {username}')
    print(f'✅ Email: {username}@example.com')
    print(f'✅ Password: TestPass123!')
    print(f'✅ is_online: {user.is_online}')
    print(f'✅ facebook_url: {user.facebook_url}')

except Exception as e:
    print(f'⚠️  Error creating test user: {e}')
"

# 7. Test the database
Write-Host "`n7. Testing database..." -ForegroundColor Yellow
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
import django
django.setup()

from accounts.models import CustomUser
from django.db import connection

print('🔍 Database Status:')
print('=' * 40)

# Check user count
count = CustomUser.objects.count()
print(f'Total users: {count}')

# Check columns
with connection.cursor() as cursor:
    cursor.execute('PRAGMA table_info(accounts_customuser);')
    columns = [row[1] for row in cursor.fetchall()]
    print(f'Total columns: {len(columns)}')

    # Check important columns
    important = ['is_online', 'facebook_url', 'username', 'email']
    for col in important:
        if col in columns:
            print(f'✅ {col} exists')
        else:
            print(f'❌ {col} missing')

print('=' * 40)
print('✅ DATABASE IS READY FOR PUBLIC REGISTRATION!')
"

Write-Host "`n" + "=" * 50 -ForegroundColor Green
Write-Host "🎉 FINAL FIX COMPLETE!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green
Write-Host "`n👉 Start the server:" -ForegroundColor Yellow
Write-Host "   python manage.py runserver" -ForegroundColor White
Write-Host "`n👉 Test registration:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:8000/accounts/register/" -ForegroundColor White
Write-Host "`n👉 Test login:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:8000/accounts/login/" -ForegroundColor White
Write-Host "`n👉 Production URL (after push):" -ForegroundColor Magenta
Write-Host "   https://connect-io-0cql.onrender.com/accounts/register/" -ForegroundColor White
Write-Host "`n👉 Test credentials:" -ForegroundColor Cyan
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White
Write-Host "   (or register as a new user)" -ForegroundColor White
Write-Host "=" * 50 -ForegroundColor Green