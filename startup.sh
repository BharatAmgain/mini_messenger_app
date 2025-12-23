#!/bin/bash
# startup.sh - OPTIMIZED FOR YOUR REQUIREMENTS - FIXED VERSION

echo "🚀 Starting Connect.io Messenger App..."

# Set Python path and environment
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Check if on Render
if [ -n "$RENDER" ]; then
    echo "🌐 Running on Render Production Environment"
    export DJANGO_SETTINGS_MODULE=messenger.settings
fi

# ====== CRITICAL: COLLECT STATIC FILES FIRST ======
echo "📁 Step 1: Collecting static files..."
python manage.py collectstatic --no-input --clear

# ====== THEN RUN MIGRATIONS ======
echo "📦 Step 2: Applying database migrations..."
python manage.py migrate --no-input

# ====== THEN CREATE USERS ======
echo "👤 Step 3: Setting up users..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user
if not User.objects.filter(username='testuser').exists():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!',
        is_verified=True,
        phone_number='+9779866399895'
    )
    print(f"✅ Created test user: testuser / TestPass123!")

# Create superuser if doesn't exist
if not User.objects.filter(is_superuser=True).exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@connect.io',
        password='AdminPass123!',
        is_verified=True
    )
    print(f"✅ Created admin user: admin / AdminPass123!")
EOF

# ====== FINALLY START SERVER ======
echo "🌐 Step 4: Starting server on port \$PORT..."

# Check if using ASGI (Channels) or WSGI
if [ -f "messenger/asgi.py" ] && grep -q "channels" requirements.txt; then
    echo "🔌 Using ASGI with Daphne (WebSockets enabled)"
    exec daphne -b 0.0.0.0 -p "\$PORT" messenger.asgi:application
else
    echo "🔌 Using WSGI with Gunicorn"
    exec gunicorn messenger.wsgi:application \
        --bind 0.0.0.0:"\$PORT" \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi