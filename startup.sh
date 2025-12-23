#!/bin/bash
# startup.sh - FIXED VERSION

echo "🚀 Starting Connect.io Messenger App..."

# Set Python path and environment
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Check if on Render
if [ -n "$RENDER" ]; then
    echo "🌐 Running on Render Production Environment"
    export DJANGO_SETTINGS_MODULE=messenger.settings
fi

# ====== CRITICAL: CREATE STATIC DIRECTORIES FIRST ======
echo "📁 Step 1: Creating static and media directories..."
mkdir -p static static/images static/js media

# ====== CREATE DEFAULT AVATAR IF NOT EXISTS ======
if [ ! -f "static/images/default-avatar.png" ]; then
    echo "🖼️  Creating default avatar placeholder..."
    # Create a simple placeholder using ImageMagick or fallback
    if command -v convert &> /dev/null; then
        convert -size 100x100 xc:#cccccc -pointsize 20 -fill white -gravity center -draw "text 0,0 'Avatar'" static/images/default-avatar.png
    else
        echo "⚠️  ImageMagick not available, creating text file"
        echo "Placeholder avatar" > static/images/default-avatar.png
    fi
fi

# ====== ENSURE CSRF FIX JS EXISTS ======
if [ ! -f "static/js/csrf_fix.js" ]; then
    echo "🔧 Creating csrf_fix.js..."
    cat > static/js/csrf_fix.js << 'EOF'
// CSRF fix for Django
(function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');
    window.csrftoken = csrftoken;
})();
EOF
fi

# ====== COLLECT STATIC FILES ======
echo "📁 Step 2: Collecting static files..."
python manage.py collectstatic --no-input --clear

# ====== RUN MIGRATIONS ======
echo "📦 Step 3: Applying database migrations..."
python manage.py migrate --no-input

# ====== CREATE USERS ======
echo "👤 Step 4: Setting up users..."
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

# ====== START SERVER ======
echo "🌐 Step 5: Starting server on port \$PORT..."

# Use Gunicorn for production
exec gunicorn messenger.wsgi:application \
    --bind 0.0.0.0:"\$PORT" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -