#!/bin/bash
# startup.sh - UPDATED VERSION

echo "🚀 Starting Connect.io Messenger App..."

# Create directories if they don't exist
echo "📁 Creating required directories..."
mkdir -p static static/images static/js media media/profile_pictures logs

# Create essential static files
echo "📝 Creating essential static files..."

# Create default avatar if missing
if [ ! -f "static/images/default-avatar.png" ]; then
    echo "🖼️  Creating default avatar placeholder..."
    # Create simple text file as placeholder
    echo "Placeholder Avatar Image" > static/images/default-avatar.png
fi

# Create csrf_fix.js
cat > static/js/csrf_fix.js << 'EOF'
// CSRF Fix - Simplified Version
(function() {
    function getCookie(name) {
        let value = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    value = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return value;
    }
    window.csrftoken = getCookie('csrftoken');
    console.log('CSRF initialized');
})();
EOF

# Create service-worker.js
cat > static/js/service-worker.js << 'EOF'
// Minimal Service Worker
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
EOF

# Set permissions
chmod -R 755 static media logs

# ====== COLLECT STATIC FILES ======
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

# ====== RUN MIGRATIONS ======
echo "📦 Applying database migrations..."
python manage.py makemigrations --no-input
python manage.py migrate --no-input

# ====== CREATE DEFAULT USER ======
echo "👤 Creating default user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user if not exists
if not User.objects.filter(username='testuser').exists():
    User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!',
        is_verified=True,
        phone_number='+9779866399895'
    )
    print("✅ Created test user: testuser / TestPass123!")

# Create admin if not exists
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@connect.io',
        password='AdminPass123!',
        is_verified=True
    )
    print("✅ Created admin user: admin / AdminPass123!")
EOF

# ====== START SERVER ======
echo "🌐 Starting server on port \$PORT..."
exec gunicorn messenger.wsgi:application \
    --bind 0.0.0.0:"\$PORT" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -