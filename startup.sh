#!/bin/bash
# startup.sh

echo "🚀 Starting Connect.io Messenger App..."

# Check for manage.py
if [ -f "manage.py" ]; then
    echo "✅ Found manage.py"
else
    echo "❌ manage.py not found. Current directory:"
    pwd
    ls -la
    exit 1
fi

# Apply database migrations
echo "📦 Applying database migrations..."
python manage.py migrate --no-input

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

# Create test user if it doesn't exist
echo "👤 Creating test user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='testuser').exists():
    User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!',
        is_verified=True
    )
    print("✅ Created test user: testuser / TestPass123!")
else:
    print("✅ Test user already exists")
EOF

# Start Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn messenger.asgi:application \
    --bind 0.0.0.0:$PORT \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile -