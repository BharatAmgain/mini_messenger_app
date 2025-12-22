#!/bin/bash

echo "🚀 Starting Connect.io Messenger App..."

# Set Python path
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found!"
    exit 1
fi

echo "✅ Found manage.py"

# Apply database migrations
echo "📦 Applying database migrations..."
python manage.py migrate --no-input

# Create static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

# Create test user
echo "👤 Creating test user..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
django.setup()
from accounts.models import CustomUser
if not CustomUser.objects.filter(email='test@example.com').exists():
    user = CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!',
        phone_number='+9779866399895',
        is_verified=True
    )
    print('✅ Created test user: test@example.com / TestPass123!')
else:
    print('✅ Test user already exists')
"

# Fix URL namespaces by creating a temporary script
echo "🔧 Fixing URL namespace issues..."
cat > /tmp/fix_urls.py << 'EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')
import django
django.setup()

# Verify URLs are working
from django.urls import reverse, NoReverseMatch

urls_to_test = [
    ('accounts:login', []),
    ('accounts:register', []),
    ('chat:chat_home', []),
    ('chat:discover_users', []),
    ('accounts:profile', []),
    ('accounts:notifications', []),
]

print("Testing URL reverses...")
for url_name, args in urls_to_test:
    try:
        url = reverse(url_name, args=args)
        print(f"✅ {url_name} -> {url}")
    except NoReverseMatch as e:
        print(f"❌ {url_name}: {e}")

print("URL namespace test complete!")
EOF

python /tmp/fix_urls.py

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn messenger.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -