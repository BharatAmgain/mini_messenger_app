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

# First, check Django OTP installation
echo "🔧 Checking Django OTP installation..."
python -c "
import django_otp
print('✅ Django OTP found:', django_otp.__version__)
"

# Apply database migrations - SKIP CHECKS FIRST
echo "📦 Applying database migrations (skipping checks)..."
python manage.py migrate --no-input --skip-checks

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
try:
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
except Exception as e:
    print(f'⚠️ Error creating test user: {e}')
    print('⚠️ Continuing anyway...')
"

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